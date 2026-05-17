"""
Эксперимент 1: Структура знания — что передавать между поколениями?

Агенты решают задачу оптимизации в меняющемся мире.
Каждая "эпоха" — новый мир с другими параметрами.
Между эпохами передаётся знание разной глубины:

1. value_only       — "оптимум = X" (голое число)
2. value_weight     — "оптимум = X, уверенность W" (число + вес)
3. value_context    — "оптимум = X, найден при условиях C" (число + контекст)
4. value_alts       — "оптимум = X, отвергнуты Y, Z" (число + отвергнутые)
5. full_structure   — всё вместе
6. method_only      — "шагай в сторону градиента, корректируй" (gen11 метод)
7. method_structure — метод + контекст + альтернативы

Мир: задача оптимизации f(x) с несколькими локальными максимумами.
Между эпохами функция сдвигается.
"""

import numpy as np
from dataclasses import dataclass, field


@dataclass
class Knowledge:
    """Структурированное знание."""
    value: float = 0.0           # найденный оптимум
    weight: float = 1.0          # уверенность (0-1)
    context: dict = field(default_factory=dict)  # при каких условиях найден
    alternatives: list = field(default_factory=list)  # отвергнутые кандидаты
    method: str = 'none'         # 'none', 'gradient', 'explore_then_exploit'
    search_history: list = field(default_factory=list)  # траектория поиска


def make_landscape(seed, n_peaks=4):
    """Создать ландшафт с несколькими пиками."""
    rng = np.random.default_rng(seed)
    centers = rng.uniform(0, 10, n_peaks)
    heights = rng.uniform(1, 5, n_peaks)
    widths = rng.uniform(0.5, 2.0, n_peaks)

    def f(x):
        return sum(h * np.exp(-((x - c) / w) ** 2) for c, h, w in zip(centers, heights, widths))

    # Найти глобальный оптимум
    xs = np.linspace(0, 10, 1000)
    ys = np.array([f(x) for x in xs])
    true_opt = xs[np.argmax(ys)]

    return f, true_opt, {'centers': centers, 'heights': heights, 'widths': widths}


def search(f, n_steps=50, start=None, rng=None, inherited=None, mode='value_only'):
    """
    Поиск оптимума с использованием унаследованного знания.
    Возвращает найденный оптимум и новое знание.
    """
    if rng is None:
        rng = np.random.default_rng()

    # Начальная точка
    if inherited is not None and mode in ('value_only', 'value_weight', 'value_context',
                                           'value_alts', 'full_structure'):
        # Начать с унаследованного значения
        if mode == 'value_weight' and inherited.weight < 0.3:
            # Низкая уверенность — начать с расширенного поиска
            x = inherited.value + rng.normal(0, 3)
        elif mode == 'value_context':
            # Есть контекст — использовать если мир похож
            x = inherited.value
        elif mode == 'value_alts':
            # Есть альтернативы — проверить их тоже
            x = inherited.value
        elif mode == 'full_structure':
            x = inherited.value
        else:
            x = inherited.value
    elif start is not None:
        x = start
    else:
        x = rng.uniform(0, 10)

    x = np.clip(x, 0, 10)
    best_x = x
    best_y = f(x)
    history = [(x, best_y)]
    alternatives_found = []

    for step in range(n_steps):
        if mode in ('method_only', 'method_structure'):
            # Метод: explore → exploit
            if step < n_steps * 0.3:
                # Explore: широкий поиск
                candidate = rng.uniform(0, 10)
            else:
                # Exploit: локальный поиск вокруг лучшего
                candidate = best_x + rng.normal(0, 0.5)
        elif mode == 'value_alts' and inherited and step < len(inherited.alternatives) * 3:
            # Проверить альтернативы
            alt_idx = step // 3
            if alt_idx < len(inherited.alternatives):
                candidate = inherited.alternatives[alt_idx] + rng.normal(0, 0.3)
            else:
                candidate = best_x + rng.normal(0, 0.5)
        elif mode == 'full_structure' and inherited:
            # Полная структура: комбинация всех подходов
            if step < 5 and inherited.alternatives:
                # Сначала проверить альтернативы
                alt_idx = step % len(inherited.alternatives)
                candidate = inherited.alternatives[alt_idx] + rng.normal(0, 0.3)
            elif step < n_steps * 0.2:
                # Потом explore
                candidate = rng.uniform(0, 10)
            else:
                # Потом exploit
                candidate = best_x + rng.normal(0, 0.3)
        elif mode == 'method_structure' and inherited:
            # Метод + структура: explore с учётом контекста
            if step < 5 and inherited.alternatives:
                candidate = inherited.alternatives[step % len(inherited.alternatives)] + rng.normal(0, 0.5)
            elif step < n_steps * 0.3:
                candidate = rng.uniform(0, 10)
            else:
                candidate = best_x + rng.normal(0, 0.3)
        else:
            # Default: локальный поиск
            candidate = best_x + rng.normal(0, 1.0)

        candidate = np.clip(candidate, 0, 10)
        cy = f(candidate)

        if cy > best_y:
            # Запомнить старый лучший как альтернативу
            if best_y > 0.5:
                alternatives_found.append(best_x)
            best_x = candidate
            best_y = cy

        history.append((candidate, cy))

    # Оценить уверенность
    # Высокая если много шагов вокруг лучшего дали похожий результат
    near_best = [y for x_h, y in history if abs(x_h - best_x) < 0.5]
    weight = min(1.0, len(near_best) / 10)

    knowledge = Knowledge(
        value=best_x,
        weight=weight,
        context={'n_steps': n_steps, 'start': start or x},
        alternatives=alternatives_found[-3:],  # последние 3
        method='explore_then_exploit' if mode.startswith('method') else 'local_search',
        search_history=[(x_h, y) for x_h, y in history[::5]],  # каждый 5-й
    )

    return best_x, best_y, knowledge


def run_epochs(n_epochs=8, mode='value_only', seed=42):
    """Прогнать несколько эпох с передачей знания."""
    rng = np.random.default_rng(seed)
    inherited = None
    results = []

    for epoch in range(n_epochs):
        landscape_seed = seed * 100 + epoch
        f, true_opt, params = make_landscape(landscape_seed)

        # Поиск
        best_x, best_y, knowledge = search(
            f, n_steps=50, rng=rng, inherited=inherited, mode=mode,
        )

        # Расстояние до оптимума
        distance = abs(best_x - true_opt)
        true_y = f(true_opt)
        efficiency = best_y / true_y if true_y > 0 else 0

        results.append({
            'epoch': epoch,
            'distance': distance,
            'efficiency': efficiency,
            'best_y': best_y,
            'true_y': true_y,
        })

        # Передать знание (в зависимости от режима)
        if mode == 'value_only':
            inherited = Knowledge(value=knowledge.value)
        elif mode == 'value_weight':
            inherited = Knowledge(value=knowledge.value, weight=knowledge.weight)
        elif mode == 'value_context':
            inherited = Knowledge(value=knowledge.value, context=knowledge.context)
        elif mode == 'value_alts':
            inherited = Knowledge(value=knowledge.value, alternatives=knowledge.alternatives)
        elif mode == 'full_structure':
            inherited = knowledge
        elif mode == 'method_only':
            inherited = Knowledge(method='explore_then_exploit')
        elif mode == 'method_structure':
            inherited = knowledge
            inherited.method = 'explore_then_exploit'
        else:
            inherited = None  # no_inheritance

    return results


def main():
    modes = [
        'no_inheritance',
        'value_only',
        'value_weight',
        'value_context',
        'value_alts',
        'full_structure',
        'method_only',
        'method_structure',
    ]

    print("=== Структура знания: что передавать? ===\n")
    print(f"{'Mode':<20} {'Efficiency':>10} {'Distance':>10}")
    print("-" * 45)

    all_results = {}
    for mode in modes:
        efficiencies = []
        distances = []
        for seed in range(30):
            results = run_epochs(mode=mode, seed=seed)
            # Среднее по эпохам 2-7 (не первая — там нет наследования)
            for r in results[1:]:
                efficiencies.append(r['efficiency'])
                distances.append(r['distance'])

        avg_eff = np.mean(efficiencies)
        avg_dist = np.mean(distances)
        all_results[mode] = (avg_eff, avg_dist)
        print(f"{mode:<20} {avg_eff:>9.0%} {avg_dist:>10.2f}")

    # Ранжирование
    print("\n=== Ранжирование по эффективности ===\n")
    ranked = sorted(all_results.items(), key=lambda x: -x[1][0])
    for i, (mode, (eff, dist)) in enumerate(ranked):
        marker = " ◄" if mode in ('method_structure', 'full_structure') else ""
        print(f"  {i+1}. {mode:<20} {eff:.0%}{marker}")

    # Анализ: как эффективность меняется по эпохам?
    print("\n=== Динамика по эпохам (seed=0) ===\n")
    key_modes = ['no_inheritance', 'value_only', 'method_only', 'method_structure']
    print(f"{'Epoch':<8}", end="")
    for mode in key_modes:
        print(f"{mode:<20}", end="")
    print()
    print("-" * 88)

    epoch_data = {}
    for mode in key_modes:
        epoch_data[mode] = run_epochs(mode=mode, seed=0)

    for epoch in range(8):
        print(f"  {epoch:<6}", end="")
        for mode in key_modes:
            eff = epoch_data[mode][epoch]['efficiency']
            print(f"{eff:<20.0%}", end="")
        print()

    # Ключевой вопрос: что добавляет каждый компонент?
    print("\n=== Маргинальный вклад каждого компонента ===\n")
    base = all_results['value_only'][0]
    print(f"  Базовая (value_only):           {base:.0%}")
    print(f"  + weight:    {all_results['value_weight'][0]:.0%}  (Δ={all_results['value_weight'][0]-base:+.0%})")
    print(f"  + context:   {all_results['value_context'][0]:.0%}  (Δ={all_results['value_context'][0]-base:+.0%})")
    print(f"  + alts:      {all_results['value_alts'][0]:.0%}  (Δ={all_results['value_alts'][0]-base:+.0%})")
    print(f"  + всё:       {all_results['full_structure'][0]:.0%}  (Δ={all_results['full_structure'][0]-base:+.0%})")
    print(f"  method_only:          {all_results['method_only'][0]:.0%}  (Δ={all_results['method_only'][0]-base:+.0%})")
    print(f"  method + structure:   {all_results['method_structure'][0]:.0%}  (Δ={all_results['method_structure'][0]-base:+.0%})")


if __name__ == '__main__':
    main()
