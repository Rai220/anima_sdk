"""
Эксперимент 2: Высокая размерность — когда структура начинает помогать?

В 1D "explore then exploit" работает тривиально (98%).
В высоких измерениях explore экспоненциально дорог.

Гипотеза: при высокой размерности:
- method_only деградирует (explore слишком дорог)
- value_alts помогает (альтернативы сужают пространство)
- method_structure > method_only (структура направляет explore)

Тестируем: dimension = 1, 3, 5, 10, 20, 50
"""

import numpy as np


def make_landscape_nd(dim, seed, n_peaks=4):
    """Ландшафт в N измерениях: сумма гауссиан."""
    rng = np.random.default_rng(seed)
    centers = rng.uniform(0, 10, (n_peaks, dim))
    heights = rng.uniform(1, 5, n_peaks)
    widths = rng.uniform(1.0, 3.0, n_peaks)

    def f(x):
        x = np.array(x)
        return sum(h * np.exp(-np.sum((x - c) ** 2) / (w ** 2))
                   for c, h, w in zip(centers, heights, widths))

    # Приблизительный оптимум (лучший центр)
    best_peak = np.argmax(heights)
    true_opt = centers[best_peak]

    return f, true_opt


def search_nd(f, dim, n_steps=200, rng=None, inherited=None, mode='method_only'):
    if rng is None:
        rng = np.random.default_rng()

    # Начальная точка
    if inherited is not None and 'value' in inherited:
        x = np.array(inherited['value']) + rng.normal(0, 0.5, dim)
    else:
        x = rng.uniform(0, 10, dim)

    x = np.clip(x, 0, 10)
    best_x = x.copy()
    best_y = f(x)
    alternatives = []

    for step in range(n_steps):
        if mode == 'no_inheritance' or mode == 'value_only':
            # Локальный поиск
            candidate = best_x + rng.normal(0, 0.8, dim)

        elif mode == 'value_weight':
            if inherited and inherited.get('weight', 1.0) < 0.3:
                candidate = rng.uniform(0, 10, dim)
            else:
                candidate = best_x + rng.normal(0, 0.8, dim)

        elif mode == 'value_alts':
            if inherited and inherited.get('alts') and step < len(inherited['alts']) * 5:
                alt_idx = (step // 5) % len(inherited['alts'])
                candidate = np.array(inherited['alts'][alt_idx]) + rng.normal(0, 0.5, dim)
            else:
                candidate = best_x + rng.normal(0, 0.8, dim)

        elif mode == 'method_only':
            # Explore then exploit
            if step < n_steps * 0.3:
                candidate = rng.uniform(0, 10, dim)
            else:
                candidate = best_x + rng.normal(0, 0.5, dim)

        elif mode == 'method_structure':
            # Метод + альтернативы: explore с приоритетом
            if inherited and inherited.get('alts') and step < len(inherited['alts']) * 3:
                alt_idx = (step // 3) % len(inherited['alts'])
                candidate = np.array(inherited['alts'][alt_idx]) + rng.normal(0, 1.0, dim)
            elif step < n_steps * 0.3:
                candidate = rng.uniform(0, 10, dim)
            else:
                candidate = best_x + rng.normal(0, 0.5, dim)

        elif mode == 'method_context':
            # Метод + контекст: адаптировать explore radius
            if inherited and inherited.get('context'):
                # Знаем масштаб прошлого мира → адаптируем радиус
                prev_spread = inherited['context'].get('spread', 5.0)
                explore_radius = prev_spread * 0.5
            else:
                explore_radius = 5.0

            if step < n_steps * 0.3:
                candidate = best_x + rng.normal(0, explore_radius, dim)
            else:
                candidate = best_x + rng.normal(0, 0.5, dim)

        elif mode == 'full':
            # Всё вместе
            if inherited and inherited.get('alts') and step < len(inherited['alts']) * 3:
                alt_idx = (step // 3) % len(inherited['alts'])
                candidate = np.array(inherited['alts'][alt_idx]) + rng.normal(0, 0.8, dim)
            elif step < n_steps * 0.3:
                if inherited and inherited.get('context'):
                    spread = inherited['context'].get('spread', 5.0)
                    candidate = best_x + rng.normal(0, spread * 0.5, dim)
                else:
                    candidate = rng.uniform(0, 10, dim)
            else:
                candidate = best_x + rng.normal(0, 0.3, dim)
        else:
            candidate = best_x + rng.normal(0, 1.0, dim)

        candidate = np.clip(candidate, 0, 10)
        cy = f(candidate)

        if cy > best_y:
            if best_y > 0.3:
                alternatives.append(best_x.tolist())
            best_x = candidate.copy()
            best_y = cy

    # Вычислить spread (для контекста)
    spread = float(np.std([a[0] for a in alternatives]) if alternatives else 5.0)

    knowledge = {
        'value': best_x.tolist(),
        'weight': min(1.0, best_y / 3.0),
        'alts': [a for a in alternatives[-5:]],  # последние 5
        'context': {'spread': spread, 'dim': dim},
    }

    return best_x, best_y, knowledge


def run_epochs_nd(dim, n_epochs=8, mode='method_only', seed=42, n_steps=200):
    rng = np.random.default_rng(seed)
    inherited = None
    results = []

    for epoch in range(n_epochs):
        f, true_opt = make_landscape_nd(dim, seed=seed * 100 + epoch)

        best_x, best_y, knowledge = search_nd(
            f, dim, n_steps=n_steps, rng=rng, inherited=inherited, mode=mode,
        )

        true_y = f(true_opt)
        efficiency = best_y / true_y if true_y > 0 else 0

        results.append({'epoch': epoch, 'efficiency': efficiency})

        # Передать знание
        if mode == 'no_inheritance':
            inherited = None
        elif mode == 'value_only':
            inherited = {'value': knowledge['value']}
        elif mode == 'value_weight':
            inherited = {'value': knowledge['value'], 'weight': knowledge['weight']}
        elif mode == 'value_alts':
            inherited = {'value': knowledge['value'], 'alts': knowledge['alts']}
        elif mode == 'method_only':
            inherited = {}  # метод встроен, ничего не передаём
        elif mode == 'method_structure':
            inherited = {'alts': knowledge['alts']}
        elif mode == 'method_context':
            inherited = {'context': knowledge['context']}
        elif mode == 'full':
            inherited = knowledge

    return results


def main():
    dims = [1, 3, 5, 10, 20, 50]
    modes = ['no_inheritance', 'value_only', 'value_alts', 'method_only',
             'method_structure', 'method_context', 'full']

    print("=== Размерность vs структура знания ===\n")

    # Таблица: dim × mode
    header = f"{'dim':<6}" + "".join(f"{m:<18}" for m in modes)
    print(header)
    print("-" * len(header))

    results_matrix = {}
    for dim in dims:
        row = f"{dim:<6}"
        for mode in modes:
            effs = []
            n_seeds = 20 if dim <= 10 else 10
            for seed in range(n_seeds):
                res = run_epochs_nd(dim, mode=mode, seed=seed, n_steps=max(200, dim * 20))
                for r in res[1:]:  # пропустить первую эпоху
                    effs.append(r['efficiency'])
            avg = np.mean(effs)
            results_matrix[(dim, mode)] = avg
            row += f"{avg:<18.0%}"
        print(row)

    # Анализ: при какой размерности структура начинает помогать?
    print("\n=== Когда structure помогает method? ===\n")
    print(f"{'dim':<6} {'method':>8} {'m+struct':>8} {'m+ctx':>8} {'full':>8} {'Δ best':>8}")
    print("-" * 50)
    for dim in dims:
        mo = results_matrix[(dim, 'method_only')]
        ms = results_matrix[(dim, 'method_structure')]
        mc = results_matrix[(dim, 'method_context')]
        fu = results_matrix[(dim, 'full')]
        best_struct = max(ms, mc, fu)
        delta = best_struct - mo
        marker = " ←" if delta > 0.03 else ""
        print(f"{dim:<6} {mo:>7.0%} {ms:>8.0%} {mc:>8.0%} {fu:>8.0%} {delta:>+7.0%}{marker}")


if __name__ == '__main__':
    main()
