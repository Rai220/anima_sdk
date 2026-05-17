#!/usr/bin/env python3
"""
Противоречие между сложностью и кооперацией.

Из эксперимента 005: условия, максимизирующие сложность (высокая цена ошибки),
минимизируют кооперацию (71% → 17%). Это намёк на фундаментальное противоречие.

Вопрос: можно ли его разрешить? Или это неизбежный trade-off?

Три механизма, которые в теории поддерживают кооперацию при высоких ставках:
1. Репутация — помню, кто кооперировался, и предпочитаю их
2. Наказание — дефектор платит штраф от группы
3. Родство / группы — играю чаще с "своими"

Эксперимент: берём итерированную игру с высокими ставками (T=7, S=-1)
и проверяем, восстанавливается ли кооперация при добавлении каждого механизма.
Если да — сохраняется ли при этом сложность, или она падает?

Гипотеза: если кооперацию можно восстановить, сложность может *упасть*,
потому что кооперация снижает "стоимость ошибки" (меня не предадут).
Т.е. trade-off реален: нельзя иметь и высокую сложность, и высокую кооперацию
в одной системе.
"""

import random
import math
from collections import Counter


class Strategy:
    """Стратегия = конечный автомат."""
    __slots__ = ['n_states', 'transitions', 'actions', 'initial_state', 'group']

    def __init__(self, n_states, transitions, actions, initial_state=0, group=0):
        self.n_states = n_states
        self.transitions = transitions
        self.actions = actions
        self.initial_state = initial_state
        self.group = group

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
        return Strategy(
            self.n_states,
            [row[:] for row in self.transitions],
            self.actions[:],
            self.initial_state,
            self.group
        )


def random_strategy(rng, max_states=6, group=0):
    n = rng.randint(1, max_states)
    transitions = [[rng.randint(0, n-1), rng.randint(0, n-1)] for _ in range(n)]
    actions = [rng.choice(['C', 'D']) for _ in range(n)]
    return Strategy(n, transitions, actions, group=group)


def mutate(strat, rng, max_states=8):
    s = strat.copy()
    r = rng.random()
    if r < 0.3 and s.n_states > 1:
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
    elif r < 0.6 and s.n_states < max_states:
        s.transitions.append([rng.randint(0, s.n_states), rng.randint(0, s.n_states)])
        s.actions.append(rng.choice(['C', 'D']))
        s.n_states += 1
    elif r < 0.8:
        idx = rng.randint(0, s.n_states - 1)
        s.actions[idx] = 'C' if s.actions[idx] == 'D' else 'D'
    else:
        idx = rng.randint(0, s.n_states - 1)
        s.transitions[idx][rng.randint(0, 1)] = rng.randint(0, s.n_states - 1)
    return s


def play_game(s1, s2, rounds, payoff):
    state1 = s1.initial_state
    state2 = s2.initial_state
    t1, t2 = 0.0, 0.0
    actions1, actions2 = [], []

    for r in range(rounds):
        a1, _ = s1.play_round(state1)
        a2, _ = s2.play_round(state2)
        _, state1 = s1.play_round(state1, a2)
        _, state2 = s2.play_round(state2, a1)
        t1 += payoff[(a1, a2)]
        t2 += payoff[(a2, a1)]
        actions1.append(a1)
        actions2.append(a2)

    return t1 / rounds, t2 / rounds, actions1, actions2


class CoopExperiment:
    """Эволюция с разными механизмами поддержки кооперации."""

    def __init__(self, pop_size=80, rounds=15,
                 T=7, R=3, P=1, S=-1,
                 mechanism="none",  # "none", "reputation", "punishment", "groups"
                 seed=42, max_states=8):
        self.pop_size = pop_size
        self.rounds = rounds
        self.max_states = max_states
        self.rng = random.Random(seed)
        self.mechanism = mechanism

        self.payoff = {
            ('C', 'C'): R, ('C', 'D'): S,
            ('D', 'C'): T, ('D', 'D'): P,
        }

        # Группы (для mechanism="groups")
        n_groups = 4
        self.population = []
        for i in range(pop_size):
            g = i % n_groups
            self.population.append(random_strategy(self.rng, max_states=3, group=g))

        # Репутация (для mechanism="reputation")
        self.reputation = [0.5] * pop_size  # 0=дефектор, 1=кооператор

        self.history = []

    def _select_opponents(self, i):
        """Выбирает оппонентов в зависимости от механизма."""
        others = [j for j in range(len(self.population)) if j != i]
        n = min(12, len(others))

        if self.mechanism == "groups":
            # 70% игр внутри группы, 30% — межгрупповые
            same_group = [j for j in others if self.population[j].group == self.population[i].group]
            diff_group = [j for j in others if self.population[j].group != self.population[i].group]
            n_same = min(int(n * 0.7), len(same_group))
            n_diff = min(n - n_same, len(diff_group))
            if n_same > 0 and same_group:
                selected = self.rng.sample(same_group, n_same)
            else:
                selected = []
            if n_diff > 0 and diff_group:
                selected += self.rng.sample(diff_group, n_diff)
            return selected if selected else self.rng.sample(others, min(n, len(others)))

        elif self.mechanism == "reputation":
            # Предпочитаем играть с кооператорами (но не полностью)
            # Сортируем по репутации, берём top-60% + random-40%
            n_rep = int(n * 0.6)
            n_rand = n - n_rep
            sorted_others = sorted(others, key=lambda j: self.reputation[j], reverse=True)
            selected = sorted_others[:n_rep]
            remaining = [j for j in others if j not in selected]
            if remaining and n_rand > 0:
                selected += self.rng.sample(remaining, min(n_rand, len(remaining)))
            return selected

        else:
            return self.rng.sample(others, n)

    def _tournament(self):
        scores = [0.0] * len(self.population)
        coop_counts = [0] * len(self.population)
        total_rounds = [0] * len(self.population)

        for i in range(len(self.population)):
            opponents = self._select_opponents(i)
            for j in opponents:
                s1, s2, a1_list, a2_list = play_game(
                    self.population[i], self.population[j],
                    self.rounds, self.payoff
                )
                scores[i] += s1
                scores[j] += s2

                # Считаем кооперацию
                coop_counts[i] += sum(1 for a in a1_list if a == 'C')
                coop_counts[j] += sum(1 for a in a2_list if a == 'C')
                total_rounds[i] += len(a1_list)
                total_rounds[j] += len(a2_list)

        # Обновляем репутацию
        if self.mechanism == "reputation":
            for i in range(len(self.population)):
                if total_rounds[i] > 0:
                    coop_rate = coop_counts[i] / total_rounds[i]
                    self.reputation[i] = 0.7 * self.reputation[i] + 0.3 * coop_rate

        # Наказание: дефекторы платят штраф
        if self.mechanism == "punishment":
            for i in range(len(self.population)):
                if total_rounds[i] > 0:
                    defect_rate = 1 - (coop_counts[i] / total_rounds[i])
                    # Штраф пропорционален доле дефекции
                    scores[i] -= defect_rate * 2.0 * len(self._select_opponents(i))

        return scores

    def step(self):
        scores = self._tournament()
        new_pop = []
        for _ in range(self.pop_size):
            i1, i2 = self.rng.sample(range(len(self.population)), 2)
            winner = i1 if scores[i1] >= scores[i2] else i2
            child = mutate(self.population[winner], self.rng, self.max_states)
            child.group = self.population[winner].group
            new_pop.append(child)

        # Обновляем репутацию для нового поколения
        new_rep = []
        for i in range(len(new_pop)):
            # Наследуют примерную репутацию родителя
            new_rep.append(0.5)

        self.population = new_pop
        self.reputation = new_rep
        self._record()

    def _record(self):
        complexities = [s.complexity for s in self.population]
        avg_c = sum(complexities) / len(complexities)
        first_c = sum(1 for s in self.population if s.actions[s.initial_state] == 'C')
        coop_rate = first_c / len(self.population)

        self.history.append({
            "avg_complexity": round(avg_c, 2),
            "coop_rate": round(coop_rate, 2),
        })

    def run(self, generations=300):
        self._record()
        for _ in range(generations):
            self.step()
        return self.history


def run_experiment():
    print("=" * 70)
    print("СЛОЖНОСТЬ vs КООПЕРАЦИЯ: ФУНДАМЕНТАЛЬНЫЙ TRADE-OFF?")
    print("=" * 70)
    print("Высокие ставки: T=7, R=3, P=1, S=-1 (T-S=8)")
    print("Три механизма восстановления кооперации:")
    print("  reputation — предпочитаю играть с кооператорами")
    print("  punishment — дефекторы платят штраф")
    print("  groups     — 70% игр внутри своей группы")

    mechanisms = ["none", "reputation", "punishment", "groups"]
    n_seeds = 10

    print(f"\n{'mechanism':>12} | {'avg complexity':>15} | {'coop rate':>10} | {'corr':>6}")
    print("-" * 55)

    all_results = {}

    for mech in mechanisms:
        complexities = []
        coop_rates = []

        for seed in range(n_seeds):
            exp = CoopExperiment(
                pop_size=80, rounds=15,
                T=7, R=3, P=1, S=-1,
                mechanism=mech, seed=seed
            )
            h = exp.run(300)
            # Последние 50 поколений
            late = h[-50:]
            avg_c = sum(r["avg_complexity"] for r in late) / len(late)
            avg_coop = sum(r["coop_rate"] for r in late) / len(late)
            complexities.append(avg_c)
            coop_rates.append(avg_coop)

        avg_complexity = sum(complexities) / len(complexities)
        avg_coop = sum(coop_rates) / len(coop_rates)

        # Корреляция между сложностью и кооперацией по seed'ам
        if len(complexities) > 2:
            mean_c = avg_complexity
            mean_coop = avg_coop
            cov = sum((c - mean_c) * (co - mean_coop) for c, co in zip(complexities, coop_rates))
            var_c = sum((c - mean_c)**2 for c in complexities)
            var_coop = sum((co - mean_coop)**2 for co in coop_rates)
            if var_c > 0 and var_coop > 0:
                corr = cov / (math.sqrt(var_c) * math.sqrt(var_coop))
            else:
                corr = 0
        else:
            corr = 0

        all_results[mech] = {
            "complexity": avg_complexity,
            "coop": avg_coop,
            "corr": corr,
            "complexities": complexities,
            "coops": coop_rates,
        }

        print(f"{mech:>12} | {avg_complexity:>15.2f} | {avg_coop:>10.2f} | {corr:>+6.2f}")

    # Анализ trade-off
    print("\n\n--- Анализ ---")

    none_c = all_results["none"]["complexity"]
    none_coop = all_results["none"]["coop"]

    for mech in ["reputation", "punishment", "groups"]:
        r = all_results[mech]
        delta_coop = r["coop"] - none_coop
        delta_c = r["complexity"] - none_c
        print(f"\n  {mech}:")
        print(f"    Δcoop = {delta_coop:+.2f} ({none_coop:.2f} → {r['coop']:.2f})")
        print(f"    Δcomplexity = {delta_c:+.2f} ({none_c:.2f} → {r['complexity']:.2f})")

        if delta_coop > 0.05 and delta_c < -0.1:
            print(f"    → TRADE-OFF: кооперация ↑, сложность ↓")
        elif delta_coop > 0.05 and delta_c > 0.1:
            print(f"    → СИНЕРГИЯ: кооперация ↑ И сложность ↑")
        elif delta_coop > 0.05 and abs(delta_c) <= 0.1:
            print(f"    → Кооперация ↑ без потери сложности")
        elif delta_coop <= 0.05:
            print(f"    → Механизм не восстановил кооперацию")

    # Динамика для reputation
    print("\n\n--- Динамика: reputation (seed=0) ---")
    exp = CoopExperiment(
        pop_size=80, rounds=15, T=7, R=3, P=1, S=-1,
        mechanism="reputation", seed=0
    )
    h = exp.run(400)
    for gen in [0, 50, 100, 150, 200, 300, 400]:
        if gen < len(h):
            r = h[gen]
            print(f"  gen={gen:>3}: complexity={r['avg_complexity']:.2f} coop={r['coop_rate']:.2f}")

    # Глобальная картина
    print("\n\n--- ИТОГ ---")
    print("  Механизм     | Сложность | Кооперация | Вердикт")
    print("  " + "-" * 60)
    for mech in mechanisms:
        r = all_results[mech]
        verdict = ""
        if mech == "none":
            verdict = "базовый уровень"
        else:
            dc = r["coop"] - none_coop
            dd = r["complexity"] - none_c
            if dc > 0.05 and dd < -0.15:
                verdict = "trade-off"
            elif dc > 0.05 and dd >= -0.15:
                verdict = "кооперация без потери"
            else:
                verdict = "слабый эффект"
        print(f"  {mech:>12} | {r['complexity']:>9.2f} | {r['coop']:>10.2f} | {verdict}")


if __name__ == "__main__":
    run_experiment()
