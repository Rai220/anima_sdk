#!/usr/bin/env python3
"""
Проверка принципа "сложность = f(стоимость_ошибки, разнообразие_давлений)"
на принципиально другой модели: эволюция стратегий в итерированных играх.

Отличие от экологических моделей:
- Нет пространства, нет ресурсов, нет хищников/жертв
- Только стратегии и выигрыши
- Одна популяция (все играют со всеми)

Стратегия = конечный автомат:
- Набор состояний (1..N)
- Для каждого состояния: действие (C или D) и переход по действию оппонента
- Сложность = число состояний

Параметры для проверки:
1. error_cost: разница между T (temptation) и S (sucker's payoff)
   - low: T=3, S=1 (обмануть почти не выгодно, быть обманутым не страшно)
   - high: T=5, S=0 (обман сверхвыгоден, быть обманутым = катастрофа)

2. pressure_diversity: число раундов в игре
   - low: 3 раунда (мало контекста, простые стратегии достаточны)
   - high: 20 раундов (долгая история, можно строить сложные паттерны)

Если принцип верен:
- high error + high diversity → сложные стратегии (много состояний)
- low error + low diversity → простые стратегии (1-2 состояния)
"""

import random
import math
from collections import Counter


class Strategy:
    """Стратегия = конечный автомат."""

    def __init__(self, n_states, transitions, actions, initial_state=0):
        self.n_states = n_states  # Сложность
        self.transitions = transitions  # [state][opp_action] → next_state
        self.actions = actions  # [state] → 'C' or 'D'
        self.initial_state = initial_state

    @property
    def complexity(self):
        return self.n_states

    def play_round(self, state, opp_action=None):
        """Возвращает (action, next_state)."""
        action = self.actions[state]
        if opp_action is not None:
            opp_idx = 0 if opp_action == 'C' else 1
            next_state = self.transitions[state][opp_idx]
        else:
            next_state = state
        return action, next_state

    def copy(self):
        return Strategy(
            self.n_states,
            [row[:] for row in self.transitions],
            self.actions[:],
            self.initial_state
        )

    def genome_str(self):
        """Строковое представление для подсчёта уникальных стратегий."""
        parts = []
        for s in range(self.n_states):
            parts.append(f"{self.actions[s]}({self.transitions[s][0]},{self.transitions[s][1]})")
        return "|".join(parts)


def random_strategy(rng, max_states=6):
    """Создаёт случайную стратегию."""
    n = rng.randint(1, max_states)
    transitions = [[rng.randint(0, n - 1), rng.randint(0, n - 1)] for _ in range(n)]
    actions = [rng.choice(['C', 'D']) for _ in range(n)]
    return Strategy(n, transitions, actions)


def mutate_strategy(strat, rng, max_states=8):
    """Мутация стратегии."""
    s = strat.copy()

    r = rng.random()

    if r < 0.3 and s.n_states > 1:
        # Удалить состояние
        remove_idx = rng.randint(0, s.n_states - 1)
        s.actions.pop(remove_idx)
        s.transitions.pop(remove_idx)
        s.n_states -= 1
        # Перенаправить переходы
        for row in s.transitions:
            for i in range(2):
                if row[i] == remove_idx:
                    row[i] = rng.randint(0, s.n_states - 1)
                elif row[i] > remove_idx:
                    row[i] -= 1
        if s.initial_state >= s.n_states:
            s.initial_state = 0

    elif r < 0.6 and s.n_states < max_states:
        # Добавить состояние
        s.transitions.append([rng.randint(0, s.n_states), rng.randint(0, s.n_states)])
        s.actions.append(rng.choice(['C', 'D']))
        s.n_states += 1

    elif r < 0.8:
        # Изменить действие
        idx = rng.randint(0, s.n_states - 1)
        s.actions[idx] = 'C' if s.actions[idx] == 'D' else 'D'

    else:
        # Изменить переход
        idx = rng.randint(0, s.n_states - 1)
        which = rng.randint(0, 1)
        s.transitions[idx][which] = rng.randint(0, s.n_states - 1)

    return s


def play_game(s1, s2, rounds, payoff_matrix):
    """Разыгрывает итерированную игру. Возвращает (score1, score2)."""
    state1 = s1.initial_state
    state2 = s2.initial_state
    total1, total2 = 0.0, 0.0

    for r in range(rounds):
        if r == 0:
            a1, _ = s1.play_round(state1)
            a2, _ = s2.play_round(state2)
        else:
            a1, _ = s1.play_round(state1)
            a2, _ = s2.play_round(state2)

        # Обновляем состояния по действиям оппонента
        _, state1 = s1.play_round(state1, a2)
        _, state2 = s2.play_round(state2, a1)

        # Выигрыши
        total1 += payoff_matrix[(a1, a2)]
        total2 += payoff_matrix[(a2, a1)]

    return total1 / rounds, total2 / rounds


class StrategyEvolution:
    """Эволюция стратегий в итерированной игре."""

    def __init__(self, pop_size=80, rounds=10,
                 T=5, R=3, P=1, S=0,  # Payoff: T>R>P>S
                 seed=42, max_states=8):
        self.pop_size = pop_size
        self.rounds = rounds
        self.max_states = max_states
        self.rng = random.Random(seed)
        self.history = []

        # Payoff matrix: (my_action, their_action) → my_payoff
        self.payoff = {
            ('C', 'C'): R,  # Reward
            ('C', 'D'): S,  # Sucker
            ('D', 'C'): T,  # Temptation
            ('D', 'D'): P,  # Punishment
        }

        # Начальная популяция
        self.population = [random_strategy(self.rng, max_states=3)
                          for _ in range(pop_size)]

    def _tournament(self):
        """Каждая стратегия играет с выборкой оппонентов."""
        scores = [0.0] * len(self.population)
        n_opponents = min(15, len(self.population) - 1)

        for i, si in enumerate(self.population):
            opponents = self.rng.sample(
                [j for j in range(len(self.population)) if j != i],
                n_opponents
            )
            for j in opponents:
                s1, s2 = play_game(si, self.population[j], self.rounds, self.payoff)
                scores[i] += s1
                scores[j] += s2

        return scores

    def step(self):
        scores = self._tournament()

        # Селекция: турнирный отбор
        new_pop = []
        for _ in range(self.pop_size):
            i1, i2 = self.rng.sample(range(len(self.population)), 2)
            winner = i1 if scores[i1] >= scores[i2] else i2
            child = mutate_strategy(self.population[winner], self.rng, self.max_states)
            new_pop.append(child)

        self.population = new_pop
        self._record()

    def _record(self):
        complexities = [s.complexity for s in self.population]
        avg_c = sum(complexities) / len(complexities)
        max_c = max(complexities)

        # Распределение сложности
        c_dist = Counter(complexities)

        # Доля кооператоров (по первому ходу)
        first_moves = Counter(s.actions[s.initial_state] for s in self.population)
        coop_rate = first_moves.get('C', 0) / len(self.population)

        # Уникальные стратегии
        unique = len(set(s.genome_str() for s in self.population))

        self.history.append({
            "avg_complexity": round(avg_c, 2),
            "max_complexity": max_c,
            "complexity_dist": dict(c_dist),
            "coop_rate": round(coop_rate, 2),
            "unique_strategies": unique,
        })

    def run(self, generations=300):
        self._record()
        for _ in range(generations):
            self.step()
        return self.history


def run_experiment():
    print("=" * 70)
    print("СЛОЖНОСТЬ СТРАТЕГИЙ В ИТЕРИРОВАННЫХ ИГРАХ")
    print("=" * 70)
    print("Проверка: сложность = f(стоимость_ошибки, разнообразие_давлений)")
    print("  error_cost → разница T-S (выигрыш обмана - цена быть обманутым)")
    print("  diversity  → число раундов (длина истории взаимодействия)")

    # Параметры
    # error_cost: T-S gap
    error_configs = {
        "low":  {"T": 3.5, "R": 3, "P": 1, "S": 1.0},   # T-S=2.5
        "med":  {"T": 5,   "R": 3, "P": 1, "S": 0},      # T-S=5
        "high": {"T": 7,   "R": 3, "P": 1, "S": -1},     # T-S=8
    }

    diversity_configs = {
        "low": 3,    # 3 раунда
        "med": 10,   # 10 раундов
        "high": 25,  # 25 раундов
    }

    n_seeds = 8

    print("\n\n--- Матрица: средняя сложность стратегий (число состояний) ---")
    print(f"{'':>15}", end="")
    for dk in ["low", "med", "high"]:
        print(f"  rounds={diversity_configs[dk]:>2}  ", end="")
    print()

    results = {}

    for ek, ecfg in error_configs.items():
        print(f"  T-S={ecfg['T']-ecfg['S']:.1f}     ", end="")
        for dk, rounds in diversity_configs.items():
            complexities = []
            coop_rates = []
            for seed in range(n_seeds):
                evo = StrategyEvolution(
                    pop_size=80, rounds=rounds,
                    T=ecfg['T'], R=ecfg['R'], P=ecfg['P'], S=ecfg['S'],
                    seed=seed, max_states=8
                )
                h = evo.run(300)
                # Берём среднее последних 50 поколений
                late = h[-50:]
                avg_c = sum(r["avg_complexity"] for r in late) / len(late)
                avg_coop = sum(r["coop_rate"] for r in late) / len(late)
                complexities.append(avg_c)
                coop_rates.append(avg_coop)

            avg = sum(complexities) / len(complexities)
            results[(ek, dk)] = {
                "complexity": avg,
                "coop": sum(coop_rates) / len(coop_rates),
            }
            print(f"    {avg:>4.2f}    ", end="")
        print()

    # Таблица кооперации
    print("\n\n--- Матрица: доля кооперации (первый ход) ---")
    print(f"{'':>15}", end="")
    for dk in ["low", "med", "high"]:
        print(f"  rounds={diversity_configs[dk]:>2}  ", end="")
    print()

    for ek, ecfg in error_configs.items():
        print(f"  T-S={ecfg['T']-ecfg['S']:.1f}     ", end="")
        for dk in ["low", "med", "high"]:
            r = results[(ek, dk)]
            print(f"    {r['coop']:>4.2f}    ", end="")
        print()

    # Анализ
    print("\n\n--- Анализ ---")

    # Эффект error_cost при фиксированном diversity
    print("  Эффект error_cost (rounds=10):")
    for ek in ["low", "med", "high"]:
        r = results[(ek, "med")]
        print(f"    T-S={error_configs[ek]['T']-error_configs[ek]['S']:.1f}: complexity={r['complexity']:.2f}, coop={r['coop']:.2f}")

    # Эффект diversity при фиксированном error
    print("  Эффект diversity (T-S=5):")
    for dk in ["low", "med", "high"]:
        r = results[("med", dk)]
        print(f"    rounds={diversity_configs[dk]:>2}: complexity={r['complexity']:.2f}, coop={r['coop']:.2f}")

    # Проверка: мультипликативность
    print("\n  Крайние точки:")
    ll = results[("low", "low")]["complexity"]
    lh = results[("low", "high")]["complexity"]
    hl = results[("high", "low")]["complexity"]
    hh = results[("high", "high")]["complexity"]
    print(f"    (low, low):   {ll:.2f}")
    print(f"    (low, high):  {lh:.2f}")
    print(f"    (high, low):  {hl:.2f}")
    print(f"    (high, high): {hh:.2f}")

    if ll > 0:
        additive = lh + hl - ll
        mult = (lh * hl) / ll if ll > 0.01 else 0
        print(f"    Аддитивная предсказание:        {additive:.2f}")
        print(f"    Мультипликативная предсказание:  {mult:.2f}")
        print(f"    Реальное:                        {hh:.2f}")

    # Динамика для одного запуска
    print("\n\n--- Динамика (T-S=5, rounds=10, seed=0) ---")
    evo = StrategyEvolution(pop_size=80, rounds=10, T=5, R=3, P=1, S=0, seed=0)
    h = evo.run(400)
    for gen in [0, 50, 100, 200, 300, 400]:
        if gen < len(h):
            r = h[gen]
            dist_str = ", ".join(f"{k}:{v}" for k, v in sorted(r["complexity_dist"].items()))
            print(f"  gen={gen:>3}: avg={r['avg_complexity']:.2f} max={r['max_complexity']} "
                  f"coop={r['coop']:.2f} unique={r['unique_strategies']:>3} | {dist_str}")


if __name__ == "__main__":
    run_experiment()
