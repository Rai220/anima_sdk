"""
Устойчивость аттрактора муравья Лэнгтона.

Вопрос: всегда ли муравей строит шоссе, если начальная конфигурация
не пуста? Вики говорит: не доказано. Проверю вычислительно.

Эксперимент:
1. Случайные начальные конфигурации (квадраты NxN с плотностью p чёрных клеток)
2. Запускаю муравья на 50000 шагов
3. Детектирую шоссе: периодическое движение с периодом 104

Гипотеза: шоссе возникает при любой начальной конфигурации,
но время до шоссе растёт с плотностью и размером.
"""

import json
import random

def run_ant(grid_size, black_cells, max_steps=50000):
    """Запускает муравья. Возвращает (нашёл_шоссе, шаг_начала, траекторию_длин)."""
    grid = {}
    for (r, c) in black_cells:
        grid[(r, c)] = 1  # 1 = чёрная

    # Муравей стартует в центре сетки
    x, y = grid_size // 2, grid_size // 2
    dx, dy = 0, -1  # начальное направление: вверх

    # Для детекции шоссе: запоминаем позиции каждые 104 шага
    positions_at_period = []
    highway_detected = False
    highway_start = -1

    for step in range(max_steps):
        color = grid.get((x, y), 0)

        if color == 0:  # белая → поворот по часовой
            dx, dy = -dy, dx
            grid[(x, y)] = 1
        else:  # чёрная → поворот против часовой
            dx, dy = dy, -dx
            del grid[(x, y)]  # стала белой

        x += dx
        y += dy

        # Каждые 104 шага проверяем, движется ли муравей по шоссе
        if (step + 1) % 104 == 0:
            positions_at_period.append((x, y))
            n = len(positions_at_period)
            if n >= 9:
                # Проверяем последние 8 дельт
                recent = positions_at_period[-9:]
                deltas = set()
                for i in range(8):
                    d = (recent[i+1][0] - recent[i][0],
                         recent[i+1][1] - recent[i][1])
                    deltas.add(d)
                if len(deltas) == 1 and (0, 0) not in deltas:
                    highway_detected = True
                    highway_start = (step + 1) - 9 * 104
                    break

    return highway_detected, highway_start


def experiment():
    results = {}

    # Эксперимент 1: пустая сетка (базовый случай)
    print("=== Базовый случай: пустая сетка ===")
    found, start = run_ant(200, [])
    print(f"Шоссе: {'да' if found else 'нет'}, начало: шаг {start}")
    results['empty'] = {'highway': found, 'start': start}

    # Эксперимент 2: случайные конфигурации разной плотности
    print("\n=== Случайные начальные конфигурации ===")
    random.seed(42)
    densities = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5]
    patch_size = 20
    trials_per_density = 20

    results['random'] = {}
    for density in densities:
        highways = 0
        starts = []
        for trial in range(trials_per_density):
            black = []
            cx, cy = 100, 100  # центр
            for r in range(cx - patch_size // 2, cx + patch_size // 2):
                for c in range(cy - patch_size // 2, cy + patch_size // 2):
                    if random.random() < density:
                        black.append((r, c))
            found, start = run_ant(200, black)
            if found:
                highways += 1
                starts.append(start)

        avg_start = sum(starts) / len(starts) if starts else -1
        print(f"Плотность {density:.0%}: шоссе в {highways}/{trials_per_density} "
              f"({highways/trials_per_density:.0%}), среднее начало: {avg_start:.0f}")
        results['random'][str(density)] = {
            'highways': highways,
            'total': trials_per_density,
            'rate': highways / trials_per_density,
            'avg_start': avg_start
        }

    # Эксперимент 3: стены (линейные препятствия)
    print("\n=== Линейные препятствия ===")
    wall_sizes = [5, 10, 20, 40]
    results['walls'] = {}
    for size in wall_sizes:
        black = [(100, 100 + i) for i in range(size)]
        found, start = run_ant(200, black)
        print(f"Стена длины {size}: шоссе={'да' if found else 'нет'}, начало: {start}")
        results['walls'][str(size)] = {'highway': found, 'start': start}

    # Эксперимент 4: квадратные блоки
    print("\n=== Квадратные блоки ===")
    block_sizes = [3, 5, 10, 15]
    results['blocks'] = {}
    for size in block_sizes:
        black = []
        cx, cy = 100, 100
        for r in range(cx, cx + size):
            for c in range(cy, cy + size):
                black.append((r, c))
        found, start = run_ant(200, black)
        print(f"Блок {size}x{size}: шоссе={'да' if found else 'нет'}, начало: {start}")
        results['blocks'][str(size)] = {'highway': found, 'start': start}

    # Эксперимент 5: многоцветные варианты (RLR, RLLR)
    print("\n=== Многоцветные варианты ===")
    results['multicolor'] = {}
    for rule_str in ['RLR', 'RLLR', 'LLRR', 'LRRL']:
        found, start = run_multicolor(200, rule_str, max_steps=100000)
        print(f"Правило {rule_str}: шоссе={'да' if found else 'нет'}, начало: {start}")
        results['multicolor'][rule_str] = {'highway': found, 'start': start}

    return results


def run_multicolor(grid_size, rule_str, max_steps=100000):
    """Многоцветный муравей. Правило — строка из L и R."""
    n_colors = len(rule_str)
    grid = {}
    x, y = grid_size // 2, grid_size // 2
    dx, dy = 0, -1

    positions_at_period = []
    check_period = 104  # начинаем с этого, потом подстроим

    for step in range(max_steps):
        color = grid.get((x, y), 0)
        turn = rule_str[color]

        if turn == 'R':
            dx, dy = -dy, dx
        else:
            dx, dy = dy, -dx

        grid[(x, y)] = (color + 1) % n_colors
        x += dx
        y += dy

        if (step + 1) % check_period == 0:
            positions_at_period.append((x, y))
            n = len(positions_at_period)
            if n >= 9:
                recent = positions_at_period[-9:]
                deltas = set()
                for i in range(8):
                    d = (recent[i+1][0] - recent[i][0],
                         recent[i+1][1] - recent[i][1])
                    deltas.add(d)
                if len(deltas) == 1 and (0, 0) not in deltas:
                    highway_start = (step + 1) - 9 * check_period
                    return True, highway_start

    return False, -1


if __name__ == '__main__':
    results = experiment()

    # Анализ
    print("\n" + "=" * 60)
    print("АНАЛИЗ")
    print("=" * 60)

    all_random = results['random']
    all_found = all(v['rate'] == 1.0 for v in all_random.values())
    any_missed = any(v['rate'] < 1.0 for v in all_random.values())

    if all_found:
        print("Все случайные конфигурации нашли шоссе.")
    elif any_missed:
        missed = {k: v for k, v in all_random.items() if v['rate'] < 1.0}
        print(f"Не все конфигурации нашли шоссе: {missed}")

    # Корреляция плотности и времени до шоссе
    densities_sorted = sorted(all_random.keys(), key=float)
    times = [all_random[d]['avg_start'] for d in densities_sorted]
    print(f"\nВремя до шоссе по плотности:")
    for d, t in zip(densities_sorted, times):
        print(f"  {float(d):.0%}: {t:.0f} шагов")

    # Гипотеза
    if all_found and times[-1] > times[0]:
        print("\nГипотеза подтверждена: шоссе возникает всегда, "
              "но время растёт с плотностью.")
    elif all_found:
        print("\nШоссе возникает всегда, но время НЕ растёт с плотностью. "
              "Гипотеза частично опровергнута.")
    else:
        print("\nГипотеза опровергнута: шоссе возникает не всегда "
              "за 50000 шагов.")

    with open('langton_robustness_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\nРезультаты сохранены в langton_robustness_results.json")
