#!/usr/bin/env python3
"""
Как распространяется кооперация: локально, глобально или сверху?

Сравниваем четыре механизма обновления стратегий:
1. ЛОКАЛЬНЫЙ — копируй лучшего соседа (пространственная близость)
2. ГЛОБАЛЬНЫЙ — копируй лучшего на всей решётке (книга, медиа, бродкаст)
3. АВТОРИТЕТ — 5% клеток фиксированы как "проповедники" кооперации
4. СМЕШАННЫЙ — 80% локально + 20% глобально (реальный мир)

Вопрос: правда ли, что локальное влияние эффективнее глобального?
"""

import random
import json
from collections import Counter

WIDTH, HEIGHT = 50, 50
ROUNDS_PER_GAME = 5
GENERATIONS = 200
MUTATION_RATE = 0.01
NOISE = 0.05

T, R, P, S = 5, 3, 1, 0

STRATEGIES = [
    'always_cooperate', 'always_defect', 'tit_for_tat',
    'suspicious_tft', 'random', 'pavlov', 'grudger', 'tit_for_two_tats',
]

COOP_STRATS = {'always_cooperate', 'tit_for_tat', 'tit_for_two_tats', 'pavlov'}


def play_round(my_action, their_action):
    if my_action == 'C' and their_action == 'C': return R
    elif my_action == 'C' and their_action == 'D': return S
    elif my_action == 'D' and their_action == 'C': return T
    else: return P


def decide(strategy, hist_mine, hist_theirs):
    if random.random() < NOISE:
        return random.choice(['C', 'D'])
    if strategy == 'always_cooperate': return 'C'
    elif strategy == 'always_defect': return 'D'
    elif strategy == 'tit_for_tat':
        return 'C' if not hist_theirs else hist_theirs[-1]
    elif strategy == 'suspicious_tft':
        return 'D' if not hist_theirs else hist_theirs[-1]
    elif strategy == 'random': return random.choice(['C', 'D'])
    elif strategy == 'pavlov':
        if not hist_mine: return 'C'
        lp = play_round(hist_mine[-1], hist_theirs[-1])
        return hist_mine[-1] if lp >= R else ('D' if hist_mine[-1] == 'C' else 'C')
    elif strategy == 'grudger':
        return 'D' if 'D' in hist_theirs else 'C'
    elif strategy == 'tit_for_two_tats':
        if len(hist_theirs) < 2: return 'C'
        return 'D' if hist_theirs[-1] == 'D' and hist_theirs[-2] == 'D' else 'C'
    return 'C'


def play_game(sa, sb):
    ha, hb = [], []
    ta, tb = 0, 0
    for _ in range(ROUNDS_PER_GAME):
        a = decide(sa, ha, hb)
        b = decide(sb, hb, ha)
        ta += play_round(a, b)
        tb += play_round(b, a)
        ha.append(a); hb.append(b)
    return ta, tb


def get_neighbors(x, y):
    nb = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0: continue
            nb.append(((x + dx) % WIDTH, (y + dy) % HEIGHT))
    return nb


def compute_scores(grid):
    scores = [[0.0] * WIDTH for _ in range(HEIGHT)]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            for nx, ny in get_neighbors(x, y):
                sa, _ = play_game(grid[y][x], grid[ny][nx])
                scores[y][x] += sa
    return scores


def snapshot(grid):
    count = Counter()
    for row in grid:
        for s in row:
            count[s] += 1
    coop = sum(count[s] for s in COOP_STRATS) / (WIDTH * HEIGHT)
    return {
        'strategies': dict(count),
        'coop_pct': round(coop, 4),
        'top': count.most_common(1)[0][0],
    }


def run(mode, generations=GENERATIONS, seed=None):
    """
    mode: 'local', 'global', 'authority', 'mixed'
    """
    if seed is not None:
        random.seed(seed)

    grid = [[random.choice(STRATEGIES) for _ in range(WIDTH)] for _ in range(HEIGHT)]

    # Для режима authority: 5% клеток — фиксированные "проповедники"
    authorities = set()
    if mode == 'authority':
        all_pos = [(x, y) for x in range(WIDTH) for y in range(HEIGHT)]
        random.shuffle(all_pos)
        for x, y in all_pos[:int(0.05 * WIDTH * HEIGHT)]:
            authorities.add((x, y))
            grid[y][x] = 'tit_for_tat'  # проповедники используют TFT

    history = []

    for gen in range(generations):
        scores = compute_scores(grid)
        history.append(snapshot(grid))

        # Найти глобально лучшего (для global и mixed)
        global_best_score = -1
        global_best_strat = None
        if mode in ('global', 'mixed'):
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    if scores[y][x] > global_best_score:
                        global_best_score = scores[y][x]
                        global_best_strat = grid[y][x]

        new_grid = [row[:] for row in grid]
        for y in range(HEIGHT):
            for x in range(WIDTH):
                # Авторитеты не меняются
                if (x, y) in authorities:
                    continue

                if mode == 'local':
                    # Копируй лучшего соседа
                    best_s, best_st = scores[y][x], grid[y][x]
                    for nx, ny in get_neighbors(x, y):
                        if scores[ny][nx] > best_s:
                            best_s = scores[ny][nx]
                            best_st = grid[ny][nx]
                    new_strat = best_st

                elif mode == 'global':
                    # Копируй глобально лучшего
                    new_strat = global_best_strat

                elif mode == 'authority':
                    # Копируй лучшего соседа (как local)
                    best_s, best_st = scores[y][x], grid[y][x]
                    for nx, ny in get_neighbors(x, y):
                        if scores[ny][nx] > best_s:
                            best_s = scores[ny][nx]
                            best_st = grid[ny][nx]
                    new_strat = best_st

                elif mode == 'mixed':
                    # 80% — локальный, 20% — глобальный
                    if random.random() < 0.2:
                        new_strat = global_best_strat
                    else:
                        best_s, best_st = scores[y][x], grid[y][x]
                        for nx, ny in get_neighbors(x, y):
                            if scores[ny][nx] > best_s:
                                best_s = scores[ny][nx]
                                best_st = grid[ny][nx]
                        new_strat = best_st

                # Мутация
                if random.random() < MUTATION_RATE:
                    new_strat = random.choice(STRATEGIES)

                new_grid[y][x] = new_strat

        grid = new_grid

    return history


def analyze(history, label):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")

    # Траектория кооперации: 5 точек
    points = [0, 10, 50, 100, len(history)-1]
    for p in points:
        h = history[p]
        print(f"  [{p:3d}] кооп: {h['coop_pct']*100:5.1f}%  доминант: {h['top']}")

    # Скорость: когда кооперация впервые > 80%?
    first_80 = None
    for i, h in enumerate(history):
        if h['coop_pct'] >= 0.8:
            first_80 = i
            break
    print(f"  Первый раз >80%: {'поколение ' + str(first_80) if first_80 is not None else 'никогда'}")

    # Стабильность: стандартное отклонение за вторую половину
    second_half = [h['coop_pct'] for h in history[len(history)//2:]]
    mean_c = sum(second_half) / len(second_half)
    std_c = (sum((x - mean_c)**2 for x in second_half) / len(second_half)) ** 0.5
    print(f"  Стабильность (2-я полов.): среднее {mean_c*100:.1f}%, стд.откл. {std_c*100:.2f}%")

    return {
        'trajectory': [h['coop_pct'] for h in history],
        'final_coop': history[-1]['coop_pct'],
        'final_top': history[-1]['top'],
        'first_80': first_80,
        'stability_mean': round(mean_c, 4),
        'stability_std': round(std_c, 4),
    }


def main():
    print("▓" * 60)
    print("КАК РАСПРОСТРАНЯЕТСЯ КООПЕРАЦИЯ?")
    print("Сравнение механизмов влияния")
    print("▓" * 60)

    SEED = 42
    results = {}

    modes = [
        ('local', 'ЛОКАЛЬНЫЙ: копируй лучшего соседа'),
        ('global', 'ГЛОБАЛЬНЫЙ: копируй лучшего на решётке'),
        ('authority', 'АВТОРИТЕТ: 5% фиксированных TFT-проповедников'),
        ('mixed', 'СМЕШАННЫЙ: 80% локально + 20% глобально'),
    ]

    for mode, label in modes:
        history = run(mode, seed=SEED)
        results[mode] = analyze(history, label)

    # Сводка
    print(f"\n{'▓'*60}")
    print("СВОДКА")
    print(f"{'▓'*60}")

    print(f"\n{'Режим':<15} {'Кон.кооп':>10} {'Скорость':>10} {'Стабильн.':>12} {'Финал':>22}")
    print("-" * 72)
    for mode, label in modes:
        r = results[mode]
        speed = f"gen {r['first_80']}" if r['first_80'] is not None else "никогда"
        print(f"{mode:<15} {r['final_coop']*100:>9.1f}% {speed:>10} {r['stability_std']*100:>10.2f}% {r['final_top']:>22}")

    # Дополнительный эксперимент: что если глобальный — дефектор?
    print(f"\n{'='*60}")
    print("  БОНУС: Глобальная пропаганда предательства")
    print(f"{'='*60}")

    # Режим global, но начальные условия — 70% always_defect
    random.seed(SEED)
    grid_biased = [
        [('always_defect' if random.random() < 0.7 else random.choice(STRATEGIES))
         for _ in range(WIDTH)]
        for _ in range(HEIGHT)
    ]

    # Запустим local и global с этим начальным условием
    for mode_name in ['local', 'global']:
        random.seed(SEED + 100)
        grid = [row[:] for row in grid_biased]

        hist = []
        for gen in range(GENERATIONS):
            scores = compute_scores(grid)
            hist.append(snapshot(grid))

            gb_score, gb_strat = -1, None
            if mode_name == 'global':
                for y in range(HEIGHT):
                    for x in range(WIDTH):
                        if scores[y][x] > gb_score:
                            gb_score = scores[y][x]
                            gb_strat = grid[y][x]

            new_grid = [row[:] for row in grid]
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    if mode_name == 'local':
                        bs, bst = scores[y][x], grid[y][x]
                        for nx, ny in get_neighbors(x, y):
                            if scores[ny][nx] > bs:
                                bs = scores[ny][nx]
                                bst = grid[ny][nx]
                        ns = bst
                    else:
                        ns = gb_strat

                    if random.random() < MUTATION_RATE:
                        ns = random.choice(STRATEGIES)
                    new_grid[y][x] = ns
            grid = new_grid

        r = analyze(hist, f"  Из 70% предателей — {mode_name.upper()}")

    # Сохранить
    with open('experiments/propagation_data.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\nДанные сохранены в experiments/propagation_data.json")


if __name__ == '__main__':
    main()
