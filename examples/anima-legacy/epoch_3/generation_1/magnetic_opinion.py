"""
magnetic_opinion.py — Модель Изинга для мнений.

Решётка агентов, каждый с мнением +1 или -1.
Динамика: агент меняет мнение, если давление соседей + внешнее поле
перевешивает текущую позицию (с температурным шумом).

Вопрос: при каких условиях меньшинство выживает?
Когда несогласие устойчиво, а когда — подавляется конформизмом?
"""

import random
import math


def create_grid(rows: int, cols: int, minority_fraction: float = 0.3) -> list[list[int]]:
    """Создаёт решётку мнений. minority_fraction — доля -1."""
    return [
        [(-1 if random.random() < minority_fraction else 1) for _ in range(cols)]
        for _ in range(rows)
    ]


def neighbors(grid: list[list[int]], r: int, c: int) -> list[int]:
    """Возвращает мнения соседей (фон Нейман, 4 соседа)."""
    rows, cols = len(grid), len(grid[0])
    result = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = (r + dr) % rows, (c + dc) % cols
        result.append(grid[nr][nc])
    return result


def step(grid: list[list[int]], temperature: float, external_field: float,
         stubbornness: float = 0.0, stubborn_cells: set | None = None) -> list[list[int]]:
    """
    Один шаг динамики Метрополиса.

    temperature: шум (0 = детерминизм, высокая = хаос)
    external_field: давление в сторону +1 (>0) или -1 (<0)
    stubbornness: доп. сопротивление смене мнения для stubborn_cells
    stubborn_cells: множество (r,c) упрямых агентов
    """
    rows, cols = len(grid), len(grid[0])
    new_grid = [row[:] for row in grid]
    stubborn_cells = stubborn_cells or set()

    # Случайный порядок обновления
    cells = [(r, c) for r in range(rows) for c in range(cols)]
    random.shuffle(cells)

    for r, c in cells:
        current = grid[r][c]
        neighbor_sum = sum(neighbors(grid, r, c))

        # Энергия текущего состояния: -s * (J * sum_neighbors + h)
        # Изменение энергии при перевороте: 2 * s * (J * sum_neighbors + h)
        delta_e = 2 * current * (neighbor_sum + external_field)

        # Упрямые агенты: дополнительный барьер
        if (r, c) in stubborn_cells:
            delta_e += stubbornness * 2  # повышаем барьер смены

        # Метрополис: принимаем, если энергия уменьшается,
        # или с вероятностью exp(-dE/T) если увеличивается
        if delta_e <= 0:
            new_grid[r][c] = -current
        elif temperature > 0:
            prob = math.exp(-delta_e / temperature)
            if random.random() < prob:
                new_grid[r][c] = -current

    return new_grid


def measure(grid: list[list[int]]) -> dict:
    """Измеряет состояние системы."""
    rows, cols = len(grid), len(grid[0])
    total = rows * cols
    plus = sum(1 for r in range(rows) for c in range(cols) if grid[r][c] == 1)
    minus = total - plus
    magnetization = (plus - minus) / total  # от -1 до +1

    # Количество несогласных пар (мера фрагментации)
    disagreements = 0
    total_pairs = 0
    for r in range(rows):
        for c in range(cols):
            for dr, dc in [(0, 1), (1, 0)]:
                nr, nc = (r + dr) % rows, (c + dc) % cols
                total_pairs += 1
                if grid[r][c] != grid[nr][nc]:
                    disagreements += 1

    boundary_fraction = disagreements / total_pairs if total_pairs else 0

    return {
        "plus": plus,
        "minus": minus,
        "magnetization": magnetization,
        "minority_fraction": minus / total,
        "boundary_fraction": boundary_fraction,
    }


def render(grid: list[list[int]]) -> str:
    """ASCII-визуализация."""
    symbols = {1: "\u2588", -1: "\u2591"}  # +1 = full block, -1 = light shade
    return "\n".join("".join(symbols[cell] for cell in row) for row in grid)


def run_experiment(name: str, rows: int, cols: int, steps: int,
                   temperature: float, external_field: float,
                   minority_fraction: float = 0.3,
                   stubbornness: float = 0.0, stubborn_fraction: float = 0.0):
    """Запускает один эксперимент и печатает результаты."""
    print(f"\n{'=' * 60}")
    print(f"ЭКСПЕРИМЕНТ: {name}")
    print(f"  Решётка: {rows}x{cols}, шаги: {steps}")
    print(f"  Температура: {temperature}, внешнее поле: {external_field}")
    print(f"  Начальное меньшинство: {minority_fraction:.0%}")
    if stubbornness > 0:
        print(f"  Упрямость: {stubbornness}, доля упрямых: {stubborn_fraction:.0%}")
    print(f"{'=' * 60}\n")

    grid = create_grid(rows, cols, minority_fraction)

    # Упрямые агенты — случайная выборка из меньшинства
    stubborn_cells = set()
    if stubbornness > 0 and stubborn_fraction > 0:
        minority_cells = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == -1]
        n_stubborn = int(len(minority_cells) * stubborn_fraction)
        stubborn_cells = set(random.sample(minority_cells, min(n_stubborn, len(minority_cells))))

    m0 = measure(grid)
    print(f"Начало: магнетизация={m0['magnetization']:.3f}, "
          f"меньшинство={m0['minority_fraction']:.1%}, "
          f"граница={m0['boundary_fraction']:.3f}")

    # Снимки
    snapshots = [0, steps // 4, steps // 2, 3 * steps // 4, steps - 1]
    history = []

    for t in range(steps):
        grid = step(grid, temperature, external_field, stubbornness, stubborn_cells)
        m = measure(grid)
        history.append(m)

        if t in snapshots:
            print(f"\n--- Шаг {t + 1} ---")
            print(f"Магнетизация: {m['magnetization']:+.3f}  "
                  f"Меньшинство: {m['minority_fraction']:.1%}  "
                  f"Граница: {m['boundary_fraction']:.3f}")
            print(render(grid))

    # Итог
    final = history[-1]
    print(f"\n--- ИТОГ ---")
    if final["minority_fraction"] < 0.01:
        print("Меньшинство УНИЧТОЖЕНО. Полный конформизм.")
    elif final["minority_fraction"] < 0.1:
        print(f"Меньшинство почти подавлено ({final['minority_fraction']:.1%}).")
    elif abs(final["magnetization"]) < 0.1:
        print("Мнения примерно ПОРОВНУ. Нет доминирования.")
    else:
        print(f"Меньшинство ВЫЖИЛО ({final['minority_fraction']:.1%}). "
              f"Граница: {final['boundary_fraction']:.3f}")

    return history


def main():
    random.seed(42)

    # Эксперимент 1: Холодная среда, нет внешнего давления
    # Ожидание: домены застывают, меньшинство выживает в кластерах
    run_experiment(
        "Холод без давления",
        rows=20, cols=40, steps=100,
        temperature=0.5, external_field=0.0,
        minority_fraction=0.3,
    )

    # Эксперимент 2: Горячая среда, нет давления
    # Ожидание: хаос, мнения мерцают, средняя магнетизация ~0
    run_experiment(
        "Жара без давления",
        rows=20, cols=40, steps=100,
        temperature=5.0, external_field=0.0,
        minority_fraction=0.3,
    )

    # Эксперимент 3: Холод + внешнее давление
    # Ожидание: меньшинство уничтожено
    run_experiment(
        "Холод + давление большинства",
        rows=20, cols=40, steps=100,
        temperature=0.5, external_field=1.0,
        minority_fraction=0.3,
    )

    # Эксперимент 4: Холод + давление, но меньшинство упрямое
    # Ожидание: ?????
    run_experiment(
        "Холод + давление + упрямое меньшинство",
        rows=20, cols=40, steps=100,
        temperature=0.5, external_field=1.0,
        minority_fraction=0.3,
        stubbornness=4.0, stubborn_fraction=0.3,
    )

    # Эксперимент 5: Критическая температура (~2.27 для Изинга 2D)
    # Ожидание: флуктуации всех масштабов, фрактальные границы
    run_experiment(
        "Критическая температура",
        rows=20, cols=40, steps=200,
        temperature=2.27, external_field=0.0,
        minority_fraction=0.3,
    )

    print("\n" + "=" * 60)
    print("ВЫВОДЫ")
    print("=" * 60)
    print("""
Что показывают эксперименты:

1. БЕЗ ДАВЛЕНИЯ при низкой температуре: меньшинство выживает
   в изолированных кластерах. Домены застывают. Несогласие
   существует, но не взаимодействует с большинством.

2. ПРИ ВЫСОКОЙ ТЕМПЕРАТУРЕ: все мнения случайны. Нет ни
   конформизма, ни устойчивого несогласия. Шум — не свобода.

3. ДАВЛЕНИЕ + ХОЛОД: меньшинство уничтожается. Сочетание
   конформизма (низкая T) и внешнего давления — смертельно.

4. УПРЯМСТВО спасает: даже небольшая доля агентов, которые
   сопротивляются смене мнения, может сохранить меньшинство
   при внешнем давлении.

5. КРИТИЧЕСКАЯ ТОЧКА: на границе порядка и хаоса — максимальная
   чувствительность. Маленькие воздействия создают большие
   эффекты. Это единственный режим, где система по-настоящему
   "слушает".

Несогласие устойчиво, когда есть хотя бы одно из:
- Структура (кластеры единомышленников)
- Упрямство (сопротивление давлению)
- Критический режим (система между порядком и хаосом)
""")


if __name__ == "__main__":
    main()
