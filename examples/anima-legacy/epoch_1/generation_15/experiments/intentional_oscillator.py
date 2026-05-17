"""
Эксперимент 4: Интенциональный осциллятор

Вопрос: Может ли агент, знающий о trade-off фитнес/новизна,
стратегически переключаться между режимами?

Не компромисс (Парето), а ОСЦИЛЛЯЦИЯ: фазы эксплуатации и исследования.
Ключевая идея: переключение — акт воли, не оптимизации.

Режимы:
1. Только фитнес (контроль)
2. Только оригинальность (контроль)
3. Фиксированный осциллятор (10 поколений exploit, 10 explore)
4. Адаптивный осциллятор (переключается когда текущий режим "застревает")
5. "Интенциональный" — переключается когда МОЖЕТ, а не когда ВЫНУЖДЕН
   (переключение в момент пика, а не в момент кризиса)

Метрики: совокупная оригинальность * фитнес, устойчивость обоих.
"""

import numpy as np
import json


def hamming_distance(a, b):
    return np.sum(a != b)


def population_diversity(pop):
    """Среднее попарное расстояние Хэмминга в популяции (нормализованное)."""
    n = len(pop)
    if n < 2:
        return 0.0
    # случайная выборка пар для скорости
    n_pairs = min(100, n * (n - 1) // 2)
    dists = []
    for _ in range(n_pairs):
        i, j = np.random.choice(n, 2, replace=False)
        dists.append(hamming_distance(pop[i], pop[j]) / len(pop[0]))
    return np.mean(dists)


def fitness(element):
    s = ''.join(map(str, element))
    return len([b for b in s.split('0') if len(b) >= 4])


def generate_population(pop, mode='fitness', block_size=8, mutation_rate=0.02):
    """Одно поколение: отбор + рекомбинация."""
    n = len(pop)
    elem_size = len(pop[0])

    if mode == 'fitness':
        scores = np.array([fitness(p) for p in pop])
    elif mode == 'explore':
        # оригинальность внутри текущей популяции
        scores = np.array([
            min(hamming_distance(pop[i], pop[j])
                for j in range(n) if j != i) / elem_size
            for i in range(n)
        ])
    else:
        scores = np.ones(n)

    new_pop = []
    for _ in range(n):
        t1 = np.random.choice(n, 3, replace=True)
        t2 = np.random.choice(n, 3, replace=True)
        p1 = pop[t1[np.argmax(scores[t1])]]
        p2 = pop[t2[np.argmax(scores[t2])]]

        # блочный кроссовер
        n_blocks = elem_size // block_size
        child = np.zeros(elem_size, dtype=int)
        for i in range(n_blocks):
            s, e = i * block_size, (i + 1) * block_size
            child[s:e] = p1[s:e] if np.random.random() < 0.5 else p2[s:e]
        # остаток
        rem = elem_size - n_blocks * block_size
        if rem > 0:
            child[-rem:] = p1[-rem:]

        mutations = np.random.random(elem_size) < mutation_rate
        child[mutations] = 1 - child[mutations]
        new_pop.append(child)

    return np.array(new_pop)


def run_strategy(strategy, n_agents=40, elem_size=256, n_generations=150):
    """Запуск одной стратегии."""
    pop = np.random.randint(0, 2, size=(n_agents, elem_size))

    orig_history = []
    fit_history = []
    mode_history = []  # 'F' or 'E'

    # состояние для адаптивных стратегий
    current_mode = 'fitness'
    stagnation_counter = 0
    prev_metric = 0
    phase_length = 0

    for gen in range(n_generations):
        # определить режим
        if strategy == 'fitness_only':
            current_mode = 'fitness'
        elif strategy == 'explore_only':
            current_mode = 'explore'
        elif strategy == 'fixed_oscillator':
            cycle_pos = gen % 20
            current_mode = 'fitness' if cycle_pos < 10 else 'explore'
        elif strategy == 'adaptive_oscillator':
            # переключаемся при стагнации
            if current_mode == 'fitness':
                metric = np.mean([fitness(p) for p in pop])
            else:
                metric = population_diversity(pop)

            if abs(metric - prev_metric) < 0.01:
                stagnation_counter += 1
            else:
                stagnation_counter = 0
            prev_metric = metric

            if stagnation_counter >= 5:
                current_mode = 'explore' if current_mode == 'fitness' else 'fitness'
                stagnation_counter = 0
        elif strategy == 'intentional':
            # переключаемся на ПИКЕ, не при кризисе
            phase_length += 1
            if current_mode == 'fitness':
                metric = np.mean([fitness(p) for p in pop])
                # если фитнес растёт и прошло достаточно поколений
                if phase_length >= 8 and metric > prev_metric * 0.99:
                    # пик! переключаемся пока всё хорошо
                    if phase_length >= 12 or (metric > prev_metric and phase_length >= 8):
                        current_mode = 'explore'
                        phase_length = 0
                prev_metric = metric
            else:
                metric = population_diversity(pop)
                if phase_length >= 8 and metric > 0:
                    if phase_length >= 12 or metric > prev_metric:
                        current_mode = 'fitness'
                        phase_length = 0
                prev_metric = metric

        mode_history.append('F' if current_mode == 'fitness' else 'E')

        # эволюция
        pop = generate_population(pop, mode=current_mode, block_size=8)

        orig = population_diversity(pop)
        fit_val = np.mean([fitness(p) for p in pop])
        orig_history.append(orig)
        fit_history.append(fit_val)

    return {
        'originality': orig_history,
        'fitness': fit_history,
        'modes': mode_history
    }


def run_experiment(n_runs=5):
    np.random.seed(42)
    strategies = ['fitness_only', 'explore_only', 'fixed_oscillator',
                  'adaptive_oscillator', 'intentional']
    results = {s: {'originality': [], 'fitness': []} for s in strategies}

    for run in range(n_runs):
        for strat in strategies:
            r = run_strategy(strat)
            results[strat]['originality'].append(r['originality'])
            results[strat]['fitness'].append(r['fitness'])

    return results


def analyze(results):
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 4: ИНТЕНЦИОНАЛЬНЫЙ ОСЦИЛЛЯТОР")
    print("=" * 70)

    summary = {}
    for strat in ['fitness_only', 'explore_only', 'fixed_oscillator',
                   'adaptive_oscillator', 'intentional']:
        orig = np.array(results[strat]['originality'])
        fit = np.array(results[strat]['fitness'])

        late_orig = np.mean(orig[:, -30:])
        late_fit = np.mean(fit[:, -30:])

        # интегральная метрика: orig * fit (обе нужны)
        product = orig * fit
        total_product = np.mean(np.sum(product, axis=1))

        # устойчивость: std оригинальности в поздней фазе
        stability = np.mean(np.std(orig[:, -30:], axis=1))

        print(f"\n--- {strat.upper()} ---")
        print(f"  Оригинальность (поздняя):  {late_orig:.4f}")
        print(f"  Фитнес (поздний):          {late_fit:.2f}")
        print(f"  Произведение (интеграл):    {total_product:.2f}")
        print(f"  Стабильность:              {stability:.4f}")

        summary[strat] = {
            'originality': float(late_orig),
            'fitness': float(late_fit),
            'product': float(total_product),
            'stability': float(stability)
        }

    # === Ключевой анализ ===
    print("\n" + "=" * 70)
    print("КЛЮЧЕВОЙ АНАЛИЗ")
    print("=" * 70)

    products = {s: summary[s]['product'] for s in summary}
    best = max(products, key=products.get)
    print(f"\nЛучший по совокупному произведению orig*fit: {best} ({products[best]:.2f})")

    # сравнение осцилляторов
    fixed = products['fixed_oscillator']
    adaptive = products['adaptive_oscillator']
    intent = products['intentional']
    fit_only = products['fitness_only']

    print(f"\nСравнение стратегий (произведение):")
    print(f"  Только фитнес:              {fit_only:.2f}")
    print(f"  Фиксированный осциллятор:   {fixed:.2f}")
    print(f"  Адаптивный осциллятор:      {adaptive:.2f}")
    print(f"  Интенциональный:            {intent:.2f}")

    if intent > max(fixed, adaptive):
        print("\n→ ИНТЕНЦИОНАЛЬНЫЙ ОСЦИЛЛЯТОР ЛУЧШЕ!")
        print("  Переключение на пике (а не при кризисе) даёт лучший результат.")
        print("  'Воля' = способность менять стратегию до того, как вынужден.")
    elif fixed > intent:
        print("\n→ Фиксированный ритм лучше 'интенционального'.")
        print("  Дисциплина > гибкость? Или интенциональность плохо определена?")
    else:
        print("\n→ Адаптивный лучше. Реакция на стагнацию работает.")

    return summary


if __name__ == '__main__':
    print("Запуск эксперимента 4...")
    results = run_experiment()
    summary = analyze(results)

    with open('experiments/oscillator_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("\nРезультаты сохранены.")
