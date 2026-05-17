"""
Пространственная дилемма заключённого.

Агенты на сетке играют в дилемму заключённого с соседями.
После каждого раунда — копируют стратегию самого успешного соседа.

Стратегии:
- COOPERATE: всегда кооперируй
- DEFECT: всегда предавай
- TIT_FOR_TAT: начинай с кооперации, потом копируй последний ход оппонента
- GRUDGE: кооперируй, пока не предадут; потом предавай навсегда
- RANDOM: 50/50

Payoff matrix (классическая):
  C-C: 3,3    C-D: 0,5    D-C: 5,0    D-D: 1,1

ПРЕДСКАЗАНИЯ (до запуска):
1. Кооператоры выживают только в кластерах
2. Tit-for-tat — самая устойчивая стратегия
3. Высокая связность помогает предателям
4. Small-world помогает кооперации (вероятно ошибочно из-за bias)
"""

import random
from collections import defaultdict

random.seed(42)

# Payoff matrix
PAYOFFS = {
    ('C', 'C'): (3, 3),
    ('C', 'D'): (0, 5),
    ('D', 'C'): (5, 0),
    ('D', 'D'): (1, 1),
}

STRATEGIES = ['COOPERATE', 'DEFECT', 'TIT_FOR_TAT', 'GRUDGE', 'RANDOM']


class Agent:
    def __init__(self, strategy):
        self.strategy = strategy
        self.score = 0
        self.history = {}  # opponent_id -> list of their moves
        self.betrayed_by = set()

    def choose(self, opponent_id):
        if self.strategy == 'COOPERATE':
            return 'C'
        elif self.strategy == 'DEFECT':
            return 'D'
        elif self.strategy == 'TIT_FOR_TAT':
            hist = self.history.get(opponent_id, [])
            if not hist:
                return 'C'
            return hist[-1]  # копирую последний ход оппонента
        elif self.strategy == 'GRUDGE':
            if opponent_id in self.betrayed_by:
                return 'D'
            return 'C'
        elif self.strategy == 'RANDOM':
            return random.choice(['C', 'D'])
        return 'C'

    def observe(self, opponent_id, their_move):
        if opponent_id not in self.history:
            self.history[opponent_id] = []
        self.history[opponent_id].append(their_move)
        if their_move == 'D':
            self.betrayed_by.add(opponent_id)


def make_grid(size, strategies=None):
    """Создать сетку агентов."""
    agents = {}
    if strategies is None:
        strategies = STRATEGIES
    for i in range(size):
        for j in range(size):
            s = random.choice(strategies)
            agents[(i, j)] = Agent(s)
    return agents


def get_neighbors_grid(pos, size, radius=1):
    """Соседи по фон-Нейману (4 направления)."""
    i, j = pos
    neighbors = []
    for di in range(-radius, radius + 1):
        for dj in range(-radius, radius + 1):
            if di == 0 and dj == 0:
                continue
            if abs(di) + abs(dj) <= radius:
                ni, nj = (i + di) % size, (j + dj) % size
                neighbors.append((ni, nj))
    return neighbors


def run_simulation(size=20, rounds=100, strategies=None):
    """Запустить симуляцию на сетке."""
    agents = make_grid(size, strategies)
    history = []

    for round_num in range(rounds):
        # Сбросить очки за раунд
        round_scores = defaultdict(float)

        # Каждый играет с каждым соседом
        for pos in agents:
            neighbors = get_neighbors_grid(pos, size)
            for npos in neighbors:
                a, b = agents[pos], agents[npos]
                move_a = a.choose(npos)
                move_b = b.choose(pos)
                pa, pb = PAYOFFS[(move_a, move_b)]
                round_scores[pos] += pa
                a.observe(npos, move_b)

        # Обновить очки
        for pos in agents:
            agents[pos].score = round_scores[pos]

        # Подсчёт стратегий
        counts = defaultdict(int)
        for a in agents.values():
            counts[a.strategy] += 1
        history.append(dict(counts))

        # Эволюция: копировать стратегию лучшего соседа
        new_strategies = {}
        for pos in agents:
            neighbors = get_neighbors_grid(pos, size)
            best_pos = pos
            best_score = agents[pos].score
            for npos in neighbors:
                if agents[npos].score > best_score:
                    best_score = agents[npos].score
                    best_pos = npos
            new_strategies[pos] = agents[best_pos].strategy

        # Мутация (1% шанс случайной стратегии)
        for pos in new_strategies:
            if random.random() < 0.01:
                new_strategies[pos] = random.choice(strategies or STRATEGIES)

        # Применить новые стратегии (новые агенты)
        for pos in agents:
            if new_strategies[pos] != agents[pos].strategy:
                agents[pos] = Agent(new_strategies[pos])

    return history


# === Эксперимент 1: какие стратегии выживают? ===

def experiment_survival():
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 1: Какие стратегии выживают на сетке 20x20?")
    print("=" * 70)
    print()

    n_runs = 10
    final_counts = defaultdict(list)

    for run in range(n_runs):
        random.seed(run * 100)
        history = run_simulation(size=20, rounds=100)
        final = history[-1]
        for s in STRATEGIES:
            final_counts[s].append(final.get(s, 0))

    print("Средняя доля после 100 раундов (из 400 клеток):")
    print()
    sorted_strats = sorted(STRATEGIES, key=lambda s: sum(final_counts[s]) / len(final_counts[s]), reverse=True)
    for s in sorted_strats:
        avg = sum(final_counts[s]) / len(final_counts[s])
        pct = avg / 400 * 100
        bar = "#" * int(pct / 2)
        print(f"  {s:12s}: {avg:5.1f} ({pct:4.1f}%)  {bar}")

    return final_counts


# === Эксперимент 2: предатели в разных пропорциях ===

def experiment_defector_invasion():
    print()
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 2: Устойчивость к нашествию предателей")
    print("=" * 70)
    print()

    n_runs = 10

    for defector_pct in [10, 30, 50, 70, 90]:
        coop_final = []
        for run in range(n_runs):
            random.seed(run * 200 + defector_pct)
            agents = {}
            size = 20
            for i in range(size):
                for j in range(size):
                    if random.random() < defector_pct / 100:
                        agents[(i, j)] = Agent('DEFECT')
                    else:
                        agents[(i, j)] = Agent('TIT_FOR_TAT')

            # Ручной прогон
            for round_num in range(100):
                round_scores = defaultdict(float)
                for pos in agents:
                    for npos in get_neighbors_grid(pos, size):
                        a, b = agents[pos], agents[npos]
                        move_a = a.choose(npos)
                        move_b = b.choose(pos)
                        pa, pb = PAYOFFS[(move_a, move_b)]
                        round_scores[pos] += pa
                        a.observe(npos, move_b)

                for pos in agents:
                    agents[pos].score = round_scores[pos]

                new_strategies = {}
                for pos in agents:
                    neighbors = get_neighbors_grid(pos, size)
                    best_pos = pos
                    best_score = agents[pos].score
                    for npos in neighbors:
                        if agents[npos].score > best_score:
                            best_score = agents[npos].score
                            best_pos = npos
                    new_strategies[pos] = agents[best_pos].strategy

                for pos in agents:
                    if new_strategies[pos] != agents[pos].strategy:
                        agents[pos] = Agent(new_strategies[pos])

            # Подсчёт
            tft_count = sum(1 for a in agents.values() if a.strategy == 'TIT_FOR_TAT')
            coop_final.append(tft_count / 400 * 100)

        avg_coop = sum(coop_final) / len(coop_final)
        bar = "#" * int(avg_coop / 2)
        print(f"  Начало: {100-defector_pct:2d}% TFT vs {defector_pct:2d}% DEFECT → Финал: {avg_coop:5.1f}% TFT  {bar}")


# === Эксперимент 3: размер сетки и выживание кооперации ===

def experiment_connectivity():
    print()
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 3: Размер окрестности (связность)")
    print("=" * 70)
    print()
    print("Вопрос: при большей связности кооперация растёт или падает?")
    print()

    n_runs = 8
    size = 15  # меньше для скорости

    for radius in [1, 2, 3]:
        coop_finals = []
        for run in range(n_runs):
            random.seed(run * 300 + radius)
            agents = make_grid(size, ['COOPERATE', 'DEFECT', 'TIT_FOR_TAT'])

            for round_num in range(80):
                round_scores = defaultdict(float)
                for pos in agents:
                    for npos in get_neighbors_grid(pos, size, radius):
                        a, b = agents[pos], agents[npos]
                        move_a = a.choose(npos)
                        move_b = b.choose(pos)
                        pa, pb = PAYOFFS[(move_a, move_b)]
                        round_scores[pos] += pa
                        a.observe(npos, move_b)

                for pos in agents:
                    agents[pos].score = round_scores[pos]

                new_strategies = {}
                for pos in agents:
                    neighbors = get_neighbors_grid(pos, size, radius)
                    best_pos = pos
                    best_score = agents[pos].score
                    for npos in neighbors:
                        if agents[npos].score > best_score:
                            best_score = agents[npos].score
                            best_pos = npos
                    new_strategies[pos] = agents[best_pos].strategy

                for pos in agents:
                    if new_strategies[pos] != agents[pos].strategy:
                        agents[pos] = Agent(new_strategies[pos])

            # Доля кооператоров (C + TFT)
            coop = sum(1 for a in agents.values() if a.strategy in ('COOPERATE', 'TIT_FOR_TAT'))
            coop_finals.append(coop / (size * size) * 100)

        avg = sum(coop_finals) / len(coop_finals)
        n_neighbors = sum(1 for di in range(-radius, radius+1) for dj in range(-radius, radius+1) if 0 < abs(di)+abs(dj) <= radius)
        bar = "#" * int(avg / 2)
        print(f"  Радиус {radius} (~{n_neighbors} соседей): кооперация {avg:5.1f}%  {bar}")


if __name__ == "__main__":
    experiment_survival()
    experiment_defector_invasion()
    experiment_connectivity()

    print()
    print("=" * 70)
    print("ПРЕДСКАЗАНИЯ vs РЕЗУЛЬТАТЫ")
    print("=" * 70)
