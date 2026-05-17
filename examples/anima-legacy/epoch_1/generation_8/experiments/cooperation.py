#!/usr/bin/env python3
"""
Эволюция кооперации в пространственной среде.

Итерированная дилемма заключённого на 2D решётке.
Агенты играют с соседями, копируют стратегию самого успешного соседа.
Среда может меняться: шум, мутации, катастрофы.

Вопрос: при каких условиях кооперация возникает, устойчива, разрушается?
"""

import random
import json
from collections import Counter

# Параметры
WIDTH, HEIGHT = 50, 50
ROUNDS_PER_GAME = 5  # раундов в каждой встрече
GENERATIONS = 200
MUTATION_RATE = 0.01
NOISE = 0.05  # вероятность случайного действия

# Выплаты (T > R > P > S)
T, R, P, S = 5, 3, 1, 0  # temptation, reward, punishment, sucker

# Стратегии
STRATEGIES = [
    'always_cooperate',
    'always_defect',
    'tit_for_tat',
    'suspicious_tft',   # tit-for-tat, начинающий с предательства
    'random',
    'pavlov',           # win-stay, lose-shift
    'grudger',          # кооперирует, пока не предали; потом вечно предаёт
    'tit_for_two_tats', # прощает одно предательство, реагирует на два подряд
]


def play_round(my_action, their_action):
    """Возвращает выплату для первого игрока."""
    if my_action == 'C' and their_action == 'C':
        return R
    elif my_action == 'C' and their_action == 'D':
        return S
    elif my_action == 'D' and their_action == 'C':
        return T
    else:
        return P


def decide(strategy, history_mine, history_theirs, noise=NOISE):
    """Решение агента. history — список предыдущих действий."""
    # Шум: с малой вероятностью действуем случайно
    if random.random() < noise:
        return random.choice(['C', 'D'])

    if strategy == 'always_cooperate':
        return 'C'
    elif strategy == 'always_defect':
        return 'D'
    elif strategy == 'tit_for_tat':
        return 'C' if not history_theirs else history_theirs[-1]
    elif strategy == 'suspicious_tft':
        return 'D' if not history_theirs else history_theirs[-1]
    elif strategy == 'random':
        return random.choice(['C', 'D'])
    elif strategy == 'pavlov':
        if not history_mine:
            return 'C'
        last_payoff = play_round(history_mine[-1], history_theirs[-1])
        return history_mine[-1] if last_payoff >= R else ('D' if history_mine[-1] == 'C' else 'C')
    elif strategy == 'grudger':
        return 'D' if 'D' in history_theirs else 'C'
    elif strategy == 'tit_for_two_tats':
        if len(history_theirs) < 2:
            return 'C'
        return 'D' if history_theirs[-1] == 'D' and history_theirs[-2] == 'D' else 'C'
    return 'C'


def play_game(strat_a, strat_b, rounds=ROUNDS_PER_GAME):
    """Играют rounds раундов. Возвращает (score_a, score_b)."""
    hist_a, hist_b = [], []
    total_a, total_b = 0, 0
    for _ in range(rounds):
        a = decide(strat_a, hist_a, hist_b)
        b = decide(strat_b, hist_b, hist_a)
        total_a += play_round(a, b)
        total_b += play_round(b, a)
        hist_a.append(a)
        hist_b.append(b)
    return total_a, total_b


def get_neighbors(x, y, w=WIDTH, h=HEIGHT):
    """Соседи Мура (8 соседей) с периодическими границами."""
    neighbors = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            neighbors.append(((x + dx) % w, (y + dy) % h))
    return neighbors


def run_simulation(
    generations=GENERATIONS,
    mutation_rate=MUTATION_RATE,
    catastrophe_interval=0,  # 0 = нет катастроф
    catastrophe_kill=0.3,    # доля уничтоженных при катастрофе
):
    """Запускает симуляцию. Возвращает историю по поколениям."""
    # Инициализация: случайные стратегии
    grid = [[random.choice(STRATEGIES) for _ in range(WIDTH)] for _ in range(HEIGHT)]

    history = []

    for gen in range(generations):
        # Подсчёт очков
        scores = [[0.0] * WIDTH for _ in range(HEIGHT)]

        for y in range(HEIGHT):
            for x in range(WIDTH):
                for nx, ny in get_neighbors(x, y):
                    sa, sb = play_game(grid[y][x], grid[ny][nx])
                    scores[y][x] += sa

        # Запись статистики
        strat_count = Counter()
        total_coop = 0
        for y in range(HEIGHT):
            for x in range(WIDTH):
                strat_count[grid[y][x]] += 1

        # Процент кооперативных стратегий
        coop_strats = {'always_cooperate', 'tit_for_tat', 'tit_for_two_tats', 'pavlov'}
        coop_pct = sum(strat_count[s] for s in coop_strats) / (WIDTH * HEIGHT)

        history.append({
            'gen': gen,
            'strategies': dict(strat_count),
            'coop_pct': round(coop_pct, 4),
            'top_strategy': strat_count.most_common(1)[0][0],
        })

        # Катастрофа?
        if catastrophe_interval > 0 and gen > 0 and gen % catastrophe_interval == 0:
            kill_count = int(WIDTH * HEIGHT * catastrophe_kill)
            positions = [(x, y) for x in range(WIDTH) for y in range(HEIGHT)]
            random.shuffle(positions)
            for x, y in positions[:kill_count]:
                grid[y][x] = random.choice(STRATEGIES)

        # Эволюция: каждый агент смотрит на соседей, копирует лучшего
        new_grid = [row[:] for row in grid]
        for y in range(HEIGHT):
            for x in range(WIDTH):
                best_score = scores[y][x]
                best_strat = grid[y][x]
                for nx, ny in get_neighbors(x, y):
                    if scores[ny][nx] > best_score:
                        best_score = scores[ny][nx]
                        best_strat = grid[ny][nx]

                # Мутация
                if random.random() < mutation_rate:
                    best_strat = random.choice(STRATEGIES)

                new_grid[y][x] = best_strat

        grid = new_grid

    return history


def print_results(history, label=""):
    """Печатает ключевые моменты."""
    if label:
        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"{'='*60}")

    print(f"\nПоколение 0: {history[0]['strategies']}")
    print(f"  Кооперация: {history[0]['coop_pct']*100:.1f}%")

    mid = len(history) // 2
    print(f"\nПоколение {mid}: {history[mid]['strategies']}")
    print(f"  Кооперация: {history[mid]['coop_pct']*100:.1f}%")

    print(f"\nПоколение {len(history)-1}: {history[-1]['strategies']}")
    print(f"  Кооперация: {history[-1]['coop_pct']*100:.1f}%")

    # Динамика кооперации
    phases = []
    prev_coop = history[0]['coop_pct']
    for h in history[1:]:
        if abs(h['coop_pct'] - prev_coop) > 0.1:
            phases.append((h['gen'], prev_coop, h['coop_pct']))
        prev_coop = h['coop_pct']

    if phases:
        print(f"\nФазовые переходы (изменение > 10%):")
        for gen, before, after in phases:
            direction = "↑" if after > before else "↓"
            print(f"  Поколение {gen}: {before*100:.1f}% → {after*100:.1f}% {direction}")

    # Доминирующие стратегии по фазам
    print(f"\nДоминирующая стратегия по четвертям:")
    for i, q in enumerate([0, len(history)//4, len(history)//2, 3*len(history)//4, len(history)-1]):
        print(f"  [{q:3d}] {history[q]['top_strategy']} ({history[q]['coop_pct']*100:.1f}% кооп.)")


def run_experiments():
    """Серия экспериментов с разными параметрами."""

    random.seed(42)

    # Эксперимент 1: базовый
    print("\n" + "▓"*60)
    print("ЭВОЛЮЦИЯ КООПЕРАЦИИ В ПРОСТРАНСТВЕННОЙ СРЕДЕ")
    print("▓"*60)

    h1 = run_simulation()
    print_results(h1, "Эксперимент 1: Базовый (мутация 1%, шум 5%)")

    # Эксперимент 2: без мутаций
    h2 = run_simulation(mutation_rate=0)
    print_results(h2, "Эксперимент 2: Без мутаций")

    # Эксперимент 3: высокий шум
    global NOISE
    old_noise = NOISE
    NOISE = 0.2
    h3 = run_simulation()
    NOISE = old_noise
    print_results(h3, "Эксперимент 3: Высокий шум (20%)")

    # Эксперимент 4: периодические катастрофы
    h4 = run_simulation(catastrophe_interval=40)
    print_results(h4, "Эксперимент 4: Катастрофы каждые 40 поколений")

    # Эксперимент 5: без мутаций и без шума
    NOISE = 0
    h5 = run_simulation(mutation_rate=0)
    NOISE = old_noise
    print_results(h5, "Эксперимент 5: Без мутаций, без шума (детерминизм)")

    # Сводка
    print("\n" + "▓"*60)
    print("СВОДКА")
    print("▓"*60)

    experiments = [
        ("Базовый", h1),
        ("Без мутаций", h2),
        ("Высокий шум", h3),
        ("Катастрофы", h4),
        ("Детерминизм", h5),
    ]

    print(f"\n{'Эксперимент':<20} {'Нач.кооп':>10} {'Кон.кооп':>10} {'Финал':>25}")
    print("-" * 70)
    for name, h in experiments:
        print(f"{name:<20} {h[0]['coop_pct']*100:>9.1f}% {h[-1]['coop_pct']*100:>9.1f}% {h[-1]['top_strategy']:>25}")

    # Сохранить данные для анализа
    data = {}
    for name, h in experiments:
        data[name] = {
            'coop_trajectory': [entry['coop_pct'] for entry in h],
            'final_strategies': h[-1]['strategies'],
            'final_top': h[-1]['top_strategy'],
        }

    with open('experiments/cooperation_data.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("\nДанные сохранены в experiments/cooperation_data.json")


if __name__ == '__main__':
    run_experiments()
