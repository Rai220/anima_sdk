#!/usr/bin/env python3
"""
Внимание как выбор: что если агенты решают, кого слушать?

В предыдущих экспериментах топология была фиксирована:
- Локальный: слушай соседей
- Глобальный: слушай лучшего в мире
- Авторитет: фиксированные ядра

Теперь: каждый агент имеет "бюджет внимания" — набор связей,
которые он может перестраивать. Связи адаптируются: агент
укрепляет связи с теми, кто приносит пользу, и ослабляет
связи с теми, кто вредит.

Вопрос: к какой топологии сходится сеть? Возникают ли
кластеры? Эхо-камеры? Что побеждает?
"""

import random
import json
from collections import Counter, defaultdict

WIDTH, HEIGHT = 30, 30  # чуть меньше для скорости
N = WIDTH * HEIGHT
ROUNDS_PER_GAME = 5
GENERATIONS = 150
MUTATION_RATE = 0.01
NOISE = 0.05
K = 8  # количество связей на агента

T, R, P, S = 5, 3, 1, 0

STRATEGIES = [
    'always_cooperate', 'always_defect', 'tit_for_tat',
    'suspicious_tft', 'random', 'pavlov', 'grudger', 'tit_for_two_tats',
]
COOP_STRATS = {'always_cooperate', 'tit_for_tat', 'tit_for_two_tats', 'pavlov'}


def play_round(a, b):
    if a == 'C' and b == 'C': return R
    elif a == 'C' and b == 'D': return S
    elif a == 'D' and b == 'C': return T
    else: return P


def decide(strategy, hm, ht):
    if random.random() < NOISE:
        return random.choice(['C', 'D'])
    if strategy == 'always_cooperate': return 'C'
    elif strategy == 'always_defect': return 'D'
    elif strategy == 'tit_for_tat':
        return 'C' if not ht else ht[-1]
    elif strategy == 'suspicious_tft':
        return 'D' if not ht else ht[-1]
    elif strategy == 'random': return random.choice(['C', 'D'])
    elif strategy == 'pavlov':
        if not hm: return 'C'
        lp = play_round(hm[-1], ht[-1])
        return hm[-1] if lp >= R else ('D' if hm[-1] == 'C' else 'C')
    elif strategy == 'grudger':
        return 'D' if 'D' in ht else 'C'
    elif strategy == 'tit_for_two_tats':
        if len(ht) < 2: return 'C'
        return 'D' if ht[-1] == 'D' and ht[-2] == 'D' else 'C'
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


def spatial_neighbors(i):
    """Соседи на решётке (для инициализации)."""
    x, y = i % WIDTH, i // WIDTH
    nb = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0: continue
            nx, ny = (x + dx) % WIDTH, (y + dy) % HEIGHT
            nb.append(ny * WIDTH + nx)
    return nb


def run_experiment(mode, seed=42):
    """
    mode:
      'fixed_local' — фиксированные связи с соседями (контроль)
      'adaptive' — связи перестраиваются: разрывай худшую, создавай новую случайно
      'adaptive_local' — как adaptive, но новые связи — только среди соседей соседей
      'preferential' — новые связи к тем, кто успешен (глобальная информация о рейтинге)
    """
    random.seed(seed)

    strategies = [random.choice(STRATEGIES) for _ in range(N)]

    # Инициализация связей: все начинают с пространственных соседей
    connections = {}
    for i in range(N):
        nb = spatial_neighbors(i)
        connections[i] = nb[:K]  # берём первые K

    history = []

    for gen in range(GENERATIONS):
        # Играем и считаем очки
        scores = [0.0] * N
        pair_scores = defaultdict(float)  # (i, j) → score of i from playing with j

        for i in range(N):
            for j in connections[i]:
                sa, sb = play_game(strategies[i], strategies[j])
                scores[i] += sa
                pair_scores[(i, j)] += sa

        # Статистика
        strat_count = Counter(strategies)
        coop_pct = sum(strat_count[s] for s in COOP_STRATS) / N

        # Характеристики сети
        # Средний кластерный коэффициент (приблизительный)
        cluster_sample = random.sample(range(N), min(100, N))
        cluster_coeffs = []
        for i in cluster_sample:
            nb = set(connections[i])
            if len(nb) < 2:
                continue
            links = 0
            pairs = 0
            for a in nb:
                for b in nb:
                    if a < b:
                        pairs += 1
                        if b in connections[a]:
                            links += 1
            if pairs > 0:
                cluster_coeffs.append(links / pairs)

        avg_cluster = sum(cluster_coeffs) / len(cluster_coeffs) if cluster_coeffs else 0

        # Гомофилия: доля связей с агентами той же стратегии
        same_strat_links = 0
        total_links = 0
        for i in range(N):
            for j in connections[i]:
                total_links += 1
                if strategies[j] in COOP_STRATS and strategies[i] in COOP_STRATS:
                    same_strat_links += 1
                elif strategies[j] not in COOP_STRATS and strategies[i] not in COOP_STRATS:
                    same_strat_links += 1
        homophily = same_strat_links / total_links if total_links > 0 else 0

        history.append({
            'gen': gen,
            'coop_pct': round(coop_pct, 4),
            'top': strat_count.most_common(1)[0][0],
            'cluster': round(avg_cluster, 4),
            'homophily': round(homophily, 4),
        })

        # Перестройка связей (если adaptive)
        if mode in ('adaptive', 'adaptive_local', 'preferential'):
            for i in range(N):
                if len(connections[i]) < 2:
                    continue
                # Найди худшую связь
                worst_j = min(connections[i], key=lambda j: pair_scores.get((i, j), 0))
                worst_score = pair_scores.get((i, worst_j), 0)

                # Средний score от связей
                avg_score = scores[i] / len(connections[i]) if connections[i] else 0

                # Перестраивай только если худшая связь ниже среднего
                if worst_score < avg_score * 0.7:
                    connections[i].remove(worst_j)

                    if mode == 'adaptive':
                        # Новая связь: случайный агент
                        candidates = [x for x in range(N) if x != i and x not in connections[i]]
                        if candidates:
                            connections[i].append(random.choice(candidates))

                    elif mode == 'adaptive_local':
                        # Новая связь: сосед соседа
                        candidates = set()
                        for j in connections[i]:
                            for k in connections.get(j, []):
                                if k != i and k not in connections[i]:
                                    candidates.add(k)
                        if candidates:
                            connections[i].append(random.choice(list(candidates)))
                        else:
                            # fallback: случайный
                            fallback = [x for x in range(N) if x != i and x not in connections[i]]
                            if fallback:
                                connections[i].append(random.choice(fallback))

                    elif mode == 'preferential':
                        # Новая связь: пропорционально успешности
                        candidates = [x for x in range(N) if x != i and x not in connections[i]]
                        if candidates:
                            weights = [max(scores[x], 0.1) for x in candidates]
                            total_w = sum(weights)
                            r = random.random() * total_w
                            cumulative = 0
                            chosen = candidates[0]
                            for c, w in zip(candidates, weights):
                                cumulative += w
                                if cumulative >= r:
                                    chosen = c
                                    break
                            connections[i].append(chosen)

        # Эволюция стратегий: копируй лучшего из своих связей
        new_strategies = strategies[:]
        for i in range(N):
            best_s, best_st = scores[i], strategies[i]
            for j in connections[i]:
                if scores[j] > best_s:
                    best_s = scores[j]
                    best_st = strategies[j]
            if random.random() < MUTATION_RATE:
                best_st = random.choice(STRATEGIES)
            new_strategies[i] = best_st
        strategies = new_strategies

    return history


def analyze(history, label):
    print(f"\n{'='*65}")
    print(f"  {label}")
    print(f"{'='*65}")

    points = [0, 10, 50, 100, len(history)-1]
    for p in points:
        if p < len(history):
            h = history[p]
            print(f"  [{p:3d}] кооп: {h['coop_pct']*100:5.1f}%  кластер: {h['cluster']:.3f}  гомофилия: {h['homophily']:.3f}  топ: {h['top']}")

    # Скорость
    first_80 = next((i for i, h in enumerate(history) if h['coop_pct'] >= 0.8), None)
    print(f"  >80%: {'gen ' + str(first_80) if first_80 else 'никогда'}")

    # Стабильность
    second = [h['coop_pct'] for h in history[len(history)//2:]]
    mean_c = sum(second) / len(second)
    std_c = (sum((x - mean_c)**2 for x in second) / len(second)) ** 0.5
    print(f"  2-я пол.: {mean_c*100:.1f}% ± {std_c*100:.2f}%")

    return {
        'trajectory': [h['coop_pct'] for h in history],
        'cluster_trajectory': [h['cluster'] for h in history],
        'homophily_trajectory': [h['homophily'] for h in history],
        'final_coop': history[-1]['coop_pct'],
        'final_cluster': history[-1]['cluster'],
        'final_homophily': history[-1]['homophily'],
        'final_top': history[-1]['top'],
    }


def main():
    print("▓" * 65)
    print("ВНИМАНИЕ КАК ВЫБОР")
    print("Что если агенты решают, кого слушать?")
    print("▓" * 65)

    results = {}
    modes = [
        ('fixed_local', 'КОНТРОЛЬ: фиксированные связи с соседями'),
        ('adaptive', 'АДАПТИВНЫЙ: перестраивай связи случайно'),
        ('adaptive_local', 'АДАПТИВНЫЙ ЛОКАЛЬНЫЙ: перестраивай к соседям соседей'),
        ('preferential', 'ПРЕФЕРЕНЦИАЛЬНЫЙ: подключайся к успешным'),
    ]

    for mode, label in modes:
        h = run_experiment(mode)
        results[mode] = analyze(h, label)

    print(f"\n{'▓'*65}")
    print("СВОДКА")
    print(f"{'▓'*65}")

    print(f"\n{'Режим':<22} {'Кооп':>7} {'Кластер':>9} {'Гомофил.':>10} {'Топ':>22}")
    print("-" * 73)
    for mode, label in modes:
        r = results[mode]
        print(f"{mode:<22} {r['final_coop']*100:>6.1f}% {r['final_cluster']:>8.3f} {r['final_homophily']:>9.3f} {r['final_top']:>22}")

    with open('experiments/attention_data.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\nДанные сохранены в experiments/attention_data.json")


if __name__ == '__main__':
    main()
