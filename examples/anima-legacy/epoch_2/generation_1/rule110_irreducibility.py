"""
Исследование вычислительной несводимости Rule 110.

Вопрос: можно ли предсказать состояние клетки после T шагов,
не симулируя все T шагов? Или существуют "короткие пути"?

Подход:
1. Симулируем Rule 110 для разных начальных условий
2. Для каждой клетки вычисляем "конус влияния" - минимальный набор
   начальных клеток, от которых зависит её состояние
3. Если конус растёт линейно с T - несводимость полная
4. Если для некоторых конфигураций конус стабилизируется - есть предсказуемые зоны

Аналогия с Коллатцем: там mod 8 давал детерминистические зоны (glide=3),
а mod 7 давал хаотические. Есть ли аналогичный раскол в Rule 110?
"""

import json
from collections import defaultdict

# Rule 110: binary 01101110
RULE_110 = {}
for i in range(8):
    left = (i >> 2) & 1
    center = (i >> 1) & 1
    right = i & 1
    RULE_110[(left, center, right)] = (110 >> i) & 1


def step(cells, width):
    """Один шаг Rule 110 с периодическими границами."""
    new = [0] * width
    for i in range(width):
        left = cells[(i - 1) % width]
        center = cells[i]
        right = cells[(i + 1) % width]
        new[i] = RULE_110[(left, center, right)]
    return new


def simulate(initial, steps):
    """Симуляция Rule 110, возвращает все поколения."""
    width = len(initial)
    history = [initial[:]]
    current = initial[:]
    for _ in range(steps):
        current = step(current, width)
        history.append(current[:])
    return history


def compute_light_cone(width, target_cell, T):
    """
    Вычисляет конус влияния: какие начальные клетки влияют на
    состояние target_cell после T шагов.

    Метод: для каждой начальной клетки, меняем её и смотрим,
    изменится ли target_cell через T шагов. Перебираем все
    возможные начальные состояния? Нет - слишком дорого.

    Вместо этого: используем случайные начальные условия и
    статистику. Для каждой начальной клетки j, сравниваем
    состояние target_cell при оригинальном и перевёрнутом j.
    """
    import random
    random.seed(42)

    influence_count = [0] * width
    n_trials = 200

    for _ in range(n_trials):
        initial = [random.randint(0, 1) for _ in range(width)]
        history = simulate(initial, T)
        original_value = history[T][target_cell]

        for j in range(width):
            flipped = initial[:]
            flipped[j] = 1 - flipped[j]
            flipped_history = simulate(flipped, T)
            if flipped_history[T][target_cell] != original_value:
                influence_count[j] += 1

    # Нормализуем: доля случаев, когда клетка j повлияла
    influence = [c / n_trials for c in influence_count]
    return influence


def measure_cone_growth(width=101, max_T=40):
    """
    Измеряет как растёт конус влияния с временем.
    Конус = число клеток с influence > порога.
    """
    target = width // 2
    results = []

    for T in range(1, max_T + 1, 2):
        influence = compute_light_cone(width, target, T)
        # Считаем клетки с influence > 5%
        cone_size = sum(1 for x in influence if x > 0.05)
        # Максимальное расстояние влияющей клетки от target
        max_dist = 0
        for j in range(width):
            if influence[j] > 0.05:
                dist = min(abs(j - target), width - abs(j - target))
                max_dist = max(max_dist, dist)

        results.append({
            'T': T,
            'cone_size': cone_size,
            'max_distance': max_dist,
            'theoretical_max': 2 * T + 1  # скорость света = 1 клетка/шаг
        })
        print(f"T={T:3d}: cone={cone_size:3d}, max_dist={max_dist:3d}, "
              f"theoretical={2*T+1:3d}, ratio={cone_size/(2*T+1):.2f}")

    return results


def find_predictable_patterns(width=50, T=20):
    """
    Ищем начальные конфигурации, для которых центральная клетка
    предсказуема (всегда 0 или всегда 1) после T шагов.

    Аналог mod 8 → glide=3 в Коллатце: есть ли "детерминистические" паттерны?
    """
    import random
    random.seed(123)

    target = width // 2
    # Проверяем все возможные 5-клеточные паттерны вокруг центра
    # и их влияние на результат через T шагов
    pattern_results = defaultdict(list)

    n_trials = 500
    window = 5  # смотрим на 5 клеток вокруг центра

    for _ in range(n_trials):
        initial = [random.randint(0, 1) for _ in range(width)]
        history = simulate(initial, T)
        result = history[T][target]

        # Извлекаем локальный паттерн
        pattern = tuple(initial[target - window // 2 + k] for k in range(window))
        pattern_results[pattern].append(result)

    # Находим детерминистические паттерны
    deterministic = []
    chaotic = []

    for pattern, results in sorted(pattern_results.items()):
        if len(results) >= 5:  # достаточно данных
            mean = sum(results) / len(results)
            if mean < 0.1 or mean > 0.9:
                deterministic.append({
                    'pattern': ''.join(map(str, pattern)),
                    'bias': round(mean, 3),
                    'n_samples': len(results)
                })
            elif 0.3 < mean < 0.7:
                chaotic.append({
                    'pattern': ''.join(map(str, pattern)),
                    'bias': round(mean, 3),
                    'n_samples': len(results)
                })

    return deterministic, chaotic


def entropy_by_depth(width=101, T=50):
    """
    Измеряем энтропию (непредсказуемость) состояния как функцию
    глубины конуса влияния.

    Если знаем k ближайших клеток начального условия,
    какова энтропия результата?
    """
    import random
    random.seed(456)

    target = width // 2
    n_trials = 1000
    results_by_context = {}

    trials = []
    for _ in range(n_trials):
        initial = [random.randint(0, 1) for _ in range(width)]
        history = simulate(initial, T)
        result = history[T][target]
        trials.append((initial, result))

    # Для каждого радиуса контекста
    entropy_data = []
    for radius in range(0, min(T + 1, 26)):
        context_results = defaultdict(lambda: [0, 0])
        for initial, result in trials:
            context = tuple(initial[target - radius: target + radius + 1])
            context_results[context][result] += 1

        # Средняя энтропия по контекстам
        total_entropy = 0
        total_weight = 0
        for context, counts in context_results.items():
            n = sum(counts)
            if n < 2:
                continue
            p = counts[1] / n
            if 0 < p < 1:
                import math
                h = -p * math.log2(p) - (1 - p) * math.log2(1 - p)
            else:
                h = 0
            total_entropy += h * n
            total_weight += n

        avg_entropy = total_entropy / total_weight if total_weight > 0 else 0
        entropy_data.append({
            'radius': radius,
            'context_width': 2 * radius + 1,
            'avg_entropy': round(avg_entropy, 4),
            'n_contexts': len(context_results)
        })
        print(f"radius={radius:2d} (width={2*radius+1:3d}): "
              f"entropy={avg_entropy:.4f}, contexts={len(context_results)}")

    return entropy_data


if __name__ == '__main__':
    print("=" * 60)
    print("RULE 110: ИССЛЕДОВАНИЕ ВЫЧИСЛИТЕЛЬНОЙ НЕСВОДИМОСТИ")
    print("=" * 60)

    print("\n--- 1. Рост конуса влияния ---")
    cone_data = measure_cone_growth(width=61, max_T=30)

    print("\n--- 2. Детерминистические vs хаотические паттерны ---")
    det, chaos = find_predictable_patterns(width=50, T=15)
    print(f"\nДетерминистических паттернов (bias > 0.9 или < 0.1): {len(det)}")
    print(f"Хаотических паттернов (0.3 < bias < 0.7): {len(chaos)}")
    if det:
        print("Примеры детерминистических:")
        for d in det[:10]:
            print(f"  {d['pattern']} → bias={d['bias']}, n={d['n_samples']}")

    print("\n--- 3. Энтропия как функция глубины контекста ---")
    entropy_data = entropy_by_depth(width=61, T=25)

    # Сохраняем результаты
    results = {
        'cone_growth': cone_data,
        'deterministic_patterns': det,
        'chaotic_patterns': chaos,
        'entropy_by_depth': entropy_data
    }

    with open('rule110_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print("ВЫВОДЫ")
    print("=" * 60)

    # Анализ роста конуса
    if len(cone_data) >= 2:
        ratios = [d['cone_size'] / d['theoretical_max']
                  for d in cone_data if d['theoretical_max'] > 0]
        avg_ratio = sum(ratios) / len(ratios)
        print(f"\nСредний коэффициент заполнения конуса: {avg_ratio:.2f}")
        if avg_ratio > 0.7:
            print("→ Конус почти полностью заполнен. Вычислительная несводимость сильная.")
            print("  Почти каждая клетка в пределах светового конуса влияет на результат.")
        elif avg_ratio > 0.3:
            print("→ Конус частично заполнен. Есть зоны влияния и зоны безразличия.")
        else:
            print("→ Конус разреженный. Есть потенциал для коротких путей.")

    # Анализ раскола
    total_patterns = len(det) + len(chaos)
    if total_patterns > 0:
        det_frac = len(det) / total_patterns
        print(f"\nДоля детерминистических паттернов: {det_frac:.1%}")
        print(f"Доля хаотических паттернов: {1 - det_frac:.1%}")

    # Анализ энтропии
    if entropy_data:
        first_h = entropy_data[0]['avg_entropy'] if entropy_data else 0
        last_h = entropy_data[-1]['avg_entropy'] if entropy_data else 0
        print(f"\nЭнтропия без контекста: {first_h:.4f}")
        print(f"Энтропия при максимальном контексте: {last_h:.4f}")
        if last_h > 0.1:
            print("→ Даже полный световой конус не устраняет неопределённость.")
            print("  Это сильное свидетельство вычислительной несводимости.")
        else:
            print("→ Контекст полного конуса почти устраняет неопределённость.")
            print("  Несводимость ограничена.")

    print("\nРезультаты сохранены в rule110_results.json")
