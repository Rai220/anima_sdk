#!/usr/bin/env python3
"""
Эмерджентность институтов.

Эксперимент 006 показал: наказание восстанавливает кооперацию при высоких ставках.
Но наказание было навязано "сверху" — параметром модели.

Вопрос: могут ли агенты *сами* развить механизм наказания?

Модель:
- Итерированная игра с высокими ставками (T=7, S=-1)
- Стратегия = конечный автомат (как в game_complexity.py)
- НОВОЕ: у каждого агента есть дополнительный "ген" — invest_in_punishment
  (доля дохода, которую он тратит на наказание дефекторов)
- Наказание — общественное благо: все, кто вкладывается, создают "фонд",
  из которого штрафуются дефекторы. Но вкладывающие сами платят.

Это "second-order cooperation" — кооперация для поддержания кооперации.
Классически считается, что она не может возникнуть спонтанно (free rider problem
на уровне наказания). Но это в теории для рационых агентов.
В эволюции — другой ответ?

Дополнительный тест: варьируем стоимость ошибки (T-S).
Предсказание формулы: институты возникнут только при высоких ставках
(когда кооперация нужнее всего, но без институтов невозможна).
"""

import random
import math
from collections import Counter


class Agent:
    """Агент с стратегией-автоматом + склонностью к наказанию."""
    __slots__ = ['n_states', 'transitions', 'actions', 'initial_state',
                 'punish_invest', 'id']

    def __init__(self, n_states, transitions, actions, punish_invest=0.0,
                 initial_state=0, id=0):
        self.n_states = n_states
        self.transitions = transitions
        self.actions = actions
        self.initial_state = initial_state
        self.punish_invest = punish_invest  # 0.0–1.0: доля дохода на наказание
        self.id = id

    @property
    def complexity(self):
        return self.n_states

    def play_round(self, state, opp_action=None):
        action = self.actions[state]
        if opp_action is not None:
            opp_idx = 0 if opp_action == 'C' else 1
            next_state = self.transitions[state][opp_idx]
        else:
            next_state = state
        return action, next_state

    def copy(self):
        return Agent(
            self.n_states,
            [row[:] for row in self.transitions],
            self.actions[:],
            self.punish_invest,
            self.initial_state,
            self.id
        )


def random_agent(rng, max_states=5, id=0):
    n = rng.randint(1, max_states)
    trans = [[rng.randint(0, n-1), rng.randint(0, n-1)] for _ in range(n)]
    acts = [rng.choice(['C', 'D']) for _ in range(n)]
    punish = rng.random() * 0.3  # Начальная инвестиция: 0–30%
    return Agent(n, trans, acts, punish, id=id)


def mutate_agent(a, rng, max_states=8):
    s = a.copy()

    # Мутация автомата
    r = rng.random()
    if r < 0.2 and s.n_states > 1:
        idx = rng.randint(0, s.n_states - 1)
        s.actions.pop(idx)
        s.transitions.pop(idx)
        s.n_states -= 1
        for row in s.transitions:
            for i in range(2):
                if row[i] == idx:
                    row[i] = rng.randint(0, s.n_states - 1)
                elif row[i] > idx:
                    row[i] -= 1
        if s.initial_state >= s.n_states:
            s.initial_state = 0
    elif r < 0.4 and s.n_states < max_states:
        s.transitions.append([rng.randint(0, s.n_states), rng.randint(0, s.n_states)])
        s.actions.append(rng.choice(['C', 'D']))
        s.n_states += 1
    elif r < 0.6:
        idx = rng.randint(0, s.n_states - 1)
        s.actions[idx] = 'C' if s.actions[idx] == 'D' else 'D'
    elif r < 0.8:
        idx = rng.randint(0, s.n_states - 1)
        s.transitions[idx][rng.randint(0, 1)] = rng.randint(0, s.n_states - 1)
    # Мутация punish_invest
    else:
        delta = rng.gauss(0, 0.08)
        s.punish_invest = max(0.0, min(1.0, s.punish_invest + delta))

    return s


def play_game(a1, a2, rounds, payoff):
    state1 = a1.initial_state
    state2 = a2.initial_state
    t1, t2 = 0.0, 0.0
    defects1, defects2 = 0, 0

    for r in range(rounds):
        act1, _ = a1.play_round(state1)
        act2, _ = a2.play_round(state2)
        _, state1 = a1.play_round(state1, act2)
        _, state2 = a2.play_round(state2, act1)
        t1 += payoff[(act1, act2)]
        t2 += payoff[(act2, act1)]
        if act1 == 'D':
            defects1 += 1
        if act2 == 'D':
            defects2 += 1

    return t1 / rounds, t2 / rounds, defects1 / rounds, defects2 / rounds


class InstitutionEvolution:
    def __init__(self, pop_size=80, rounds=15,
                 T=7, R=3, P=1, S=-1,
                 seed=42, max_states=8):
        self.pop_size = pop_size
        self.rounds = rounds
        self.max_states = max_states
        self.rng = random.Random(seed)
        self.next_id = 0

        self.payoff = {
            ('C', 'C'): R, ('C', 'D'): S,
            ('D', 'C'): T, ('D', 'D'): P,
        }

        self.population = [self._new_agent() for _ in range(pop_size)]
        self.history = []

    def _new_agent(self):
        self.next_id += 1
        return random_agent(self.rng, max_states=3, id=self.next_id)

    def step(self):
        n = len(self.population)
        scores = [0.0] * n
        defect_rates = [0.0] * n
        game_counts = [0] * n
        n_opponents = min(12, n - 1)

        # Турнир
        for i in range(n):
            opponents = self.rng.sample([j for j in range(n) if j != i], n_opponents)
            for j in opponents:
                s1, s2, d1, d2 = play_game(
                    self.population[i], self.population[j],
                    self.rounds, self.payoff
                )
                scores[i] += s1
                scores[j] += s2
                defect_rates[i] += d1
                defect_rates[j] += d2
                game_counts[i] += 1
                game_counts[j] += 1

        # Нормируем defect rate
        for i in range(n):
            if game_counts[i] > 0:
                defect_rates[i] /= game_counts[i]

        # Наказание: общественное благо
        # Каждый вкладывает punish_invest долю своего дохода
        punishment_fund = 0.0
        contributors = 0
        for i in range(n):
            invest = self.population[i].punish_invest
            contribution = max(scores[i], 0) * invest
            scores[i] -= contribution  # Платит из своего дохода
            punishment_fund += contribution
            if invest > 0.05:
                contributors += 1

        # Штраф распределяется пропорционально defect_rate
        if punishment_fund > 0:
            total_defection = sum(defect_rates)
            if total_defection > 0:
                for i in range(n):
                    penalty = punishment_fund * (defect_rates[i] / total_defection)
                    scores[i] -= penalty

        # Селекция
        new_pop = []
        for _ in range(self.pop_size):
            i1, i2 = self.rng.sample(range(n), 2)
            winner = i1 if scores[i1] >= scores[i2] else i2
            child = mutate_agent(self.population[winner], self.rng, self.max_states)
            new_pop.append(child)

        self.population = new_pop
        self._record(scores, defect_rates, contributors)

    def _record(self, scores=None, defect_rates=None, contributors=0):
        n = len(self.population)
        avg_c = sum(a.complexity for a in self.population) / n
        avg_pi = sum(a.punish_invest for a in self.population) / n
        first_c = sum(1 for a in self.population if a.actions[a.initial_state] == 'C')
        coop_rate = first_c / n

        # Распределение punish_invest
        punishers = sum(1 for a in self.population if a.punish_invest > 0.1)
        high_punishers = sum(1 for a in self.population if a.punish_invest > 0.3)

        self.history.append({
            "avg_complexity": round(avg_c, 2),
            "coop_rate": round(coop_rate, 2),
            "avg_punish_invest": round(avg_pi, 3),
            "punishers_pct": round(punishers / n * 100, 1),
            "high_punishers_pct": round(high_punishers / n * 100, 1),
            "contributors": contributors,
        })

    def run(self, generations=400):
        self._record()
        for _ in range(generations):
            self.step()
        return self.history


def run_experiment():
    print("=" * 70)
    print("ЭМЕРДЖЕНТНОСТЬ ИНСТИТУТОВ")
    print("=" * 70)
    print("Могут ли агенты *сами* изобрести наказание дефекторов?")

    n_seeds = 8

    # Эксперимент 1: Возникает ли наказание при высоких ставках?
    print("\n\n--- Эксперимент 1: Высокие ставки (T=7, S=-1) ---")
    for seed in range(3):
        exp = InstitutionEvolution(T=7, R=3, P=1, S=-1, seed=seed)
        h = exp.run(400)
        print(f"\n  seed={seed}:")
        for gen in [0, 50, 100, 200, 300, 400]:
            if gen < len(h):
                r = h[gen]
                print(f"    gen={gen:>3}: complexity={r['avg_complexity']:.2f} "
                      f"coop={r['coop_rate']:.2f} "
                      f"punish_invest={r['avg_punish_invest']:.3f} "
                      f"punishers={r['punishers_pct']:.0f}%")

    # Эксперимент 2: Sweep по ставкам — при каких T-S возникают институты?
    print("\n\n--- Эксперимент 2: При каких ставках возникают институты? ---")
    ts_configs = [
        (3.5, 1.0, "T-S=2.5"),
        (5, 0, "T-S=5"),
        (7, -1, "T-S=8"),
        (9, -2, "T-S=11"),
    ]

    print(f"  {'stakes':>8} | {'complexity':>10} | {'coop':>6} | {'punish_invest':>14} | {'punishers%':>10}")
    print("  " + "-" * 65)

    for T, S, label in ts_configs:
        complexities, coops, punishes, punisher_pcts = [], [], [], []
        for seed in range(n_seeds):
            exp = InstitutionEvolution(T=T, R=3, P=1, S=S, seed=seed)
            h = exp.run(400)
            late = h[-50:]
            complexities.append(sum(r["avg_complexity"] for r in late) / len(late))
            coops.append(sum(r["coop_rate"] for r in late) / len(late))
            punishes.append(sum(r["avg_punish_invest"] for r in late) / len(late))
            punisher_pcts.append(sum(r["punishers_pct"] for r in late) / len(late))

        avg_c = sum(complexities) / len(complexities)
        avg_coop = sum(coops) / len(coops)
        avg_p = sum(punishes) / len(punishes)
        avg_pp = sum(punisher_pcts) / len(punisher_pcts)
        print(f"  {label:>8} | {avg_c:>10.2f} | {avg_coop:>6.2f} | {avg_p:>14.3f} | {avg_pp:>9.1f}%")

    # Эксперимент 3: Сравнение — с возможностью наказания vs без
    print("\n\n--- Эксперимент 3: С возможностью наказания vs без ---")

    for label, T, S in [("T-S=5", 5, 0), ("T-S=8", 7, -1)]:
        coops_with = []
        coops_without = []

        for seed in range(n_seeds):
            # С наказанием
            exp = InstitutionEvolution(T=T, R=3, P=1, S=S, seed=seed)
            h = exp.run(400)
            late = h[-50:]
            coops_with.append(sum(r["coop_rate"] for r in late) / len(late))

            # Без наказания (punish_invest всегда = 0)
            exp2 = InstitutionEvolution(T=T, R=3, P=1, S=S, seed=seed)
            # Зануляем invest
            for a in exp2.population:
                a.punish_invest = 0.0
            h2 = exp2.run(400)
            late2 = h2[-50:]
            coops_without.append(sum(r["coop_rate"] for r in late2) / len(late2))

        avg_with = sum(coops_with) / len(coops_with)
        avg_without = sum(coops_without) / len(coops_without)
        print(f"  {label}: coop_with_punishment={avg_with:.2f}, coop_without={avg_without:.2f}, Δ={avg_with - avg_without:+.2f}")

    print("\n\n--- ИТОГ ---")
    print("  Вопрос: могут ли агенты самостоятельно развить институт наказания?")


if __name__ == "__main__":
    run_experiment()
