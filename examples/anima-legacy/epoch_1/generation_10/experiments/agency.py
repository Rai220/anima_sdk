#!/usr/bin/env python3
"""
Адаптация vs Агентность.

Gen 10 показал: эволюция оптимизирует стратегии *внутри* фиксированных правил,
но не может создать институты (менять правила).

Вопрос: что происходит, когда агенты могут модифицировать саму игру?

Модель:
- Итерированная дилемма заключённого
- Два типа популяций:
  A) ADAPTERS: эволюционируют стратегию (автомат), правила фиксированы
  B) AGENTS: эволюционируют стратегию + "предложение" по изменению матрицы выигрышей

"Предложение" агента:
- Каждый агент предлагает модификацию одного элемента матрицы: T, R, P, или S
- Действующая матрица = median всех предложений (голосование)
- Т.е. агенты *коллективно* определяют правила игры

Это моделирует "проектирование": агенты не просто играют — они выбирают,
в какую игру играть. Кто-то может предложить снизить T (выгоду от обмана),
кто-то — повысить R (выгоду от взаимной кооперации).

Вопрос:
1. К какой матрице выигрышей сходятся агенты?
2. Отличается ли результат (кооперация, сложность) от фиксированных правил?
3. Создают ли агенты "институт" через коллективное проектирование правил?
"""

import random
import math
from collections import Counter


class Strategy:
    __slots__ = ['n_states', 'transitions', 'actions', 'initial_state',
                 'proposed_T', 'proposed_R', 'proposed_P', 'proposed_S']

    def __init__(self, n_states, transitions, actions, initial_state=0,
                 proposed_T=5.0, proposed_R=3.0, proposed_P=1.0, proposed_S=0.0):
        self.n_states = n_states
        self.transitions = transitions
        self.actions = actions
        self.initial_state = initial_state
        self.proposed_T = proposed_T
        self.proposed_R = proposed_R
        self.proposed_P = proposed_P
        self.proposed_S = proposed_S

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
            self.proposed_T, self.proposed_R, self.proposed_P, self.proposed_S
        )


def random_strategy(rng, max_states=5, has_proposals=False,
                    base_T=5, base_R=3, base_P=1, base_S=0):
    n = rng.randint(1, max_states)
    trans = [[rng.randint(0, n-1), rng.randint(0, n-1)] for _ in range(n)]
    acts = [rng.choice(['C', 'D']) for _ in range(n)]
    if has_proposals:
        pT = base_T + rng.gauss(0, 1)
        pR = base_R + rng.gauss(0, 0.5)
        pP = base_P + rng.gauss(0, 0.5)
        pS = base_S + rng.gauss(0, 0.5)
    else:
        pT, pR, pP, pS = base_T, base_R, base_P, base_S
    return Strategy(n, trans, acts, proposed_T=pT, proposed_R=pR, proposed_P=pP, proposed_S=pS)


def mutate(strat, rng, max_states=8, mutate_proposals=False):
    s = strat.copy()
    r = rng.random()
    if r < 0.25 and s.n_states > 1:
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
    elif r < 0.5 and s.n_states < max_states:
        s.transitions.append([rng.randint(0, s.n_states), rng.randint(0, s.n_states)])
        s.actions.append(rng.choice(['C', 'D']))
        s.n_states += 1
    elif r < 0.7:
        idx = rng.randint(0, s.n_states - 1)
        s.actions[idx] = 'C' if s.actions[idx] == 'D' else 'D'
    elif r < 0.85:
        idx = rng.randint(0, s.n_states - 1)
        s.transitions[idx][rng.randint(0, 1)] = rng.randint(0, s.n_states - 1)
    elif mutate_proposals:
        # Мутация предложений
        which = rng.choice(['T', 'R', 'P', 'S'])
        delta = rng.gauss(0, 0.3)
        if which == 'T':
            s.proposed_T = max(0, s.proposed_T + delta)
        elif which == 'R':
            s.proposed_R = max(0, s.proposed_R + delta)
        elif which == 'P':
            s.proposed_P = max(0, s.proposed_P + delta)
        else:
            s.proposed_S = s.proposed_S + delta  # S can be negative
    return s


def play_game(s1, s2, rounds, payoff):
    state1, state2 = s1.initial_state, s2.initial_state
    t1, t2 = 0.0, 0.0
    for _ in range(rounds):
        a1, _ = s1.play_round(state1)
        a2, _ = s2.play_round(state2)
        _, state1 = s1.play_round(state1, a2)
        _, state2 = s2.play_round(state2, a1)
        t1 += payoff[(a1, a2)]
        t2 += payoff[(a2, a1)]
    return t1 / rounds, t2 / rounds


def median(values):
    s = sorted(values)
    n = len(s)
    if n % 2 == 0:
        return (s[n//2 - 1] + s[n//2]) / 2
    return s[n//2]


class AgencyExperiment:
    def __init__(self, pop_size=80, rounds=15,
                 base_T=7, base_R=3, base_P=1, base_S=-1,
                 agent_mode=False,  # True = agents can propose rules
                 seed=42, max_states=8):
        self.pop_size = pop_size
        self.rounds = rounds
        self.max_states = max_states
        self.rng = random.Random(seed)
        self.agent_mode = agent_mode
        self.base_T = base_T
        self.base_R = base_R
        self.base_P = base_P
        self.base_S = base_S

        self.population = [
            random_strategy(self.rng, max_states=3, has_proposals=agent_mode,
                          base_T=base_T, base_R=base_R, base_P=base_P, base_S=base_S)
            for _ in range(pop_size)
        ]
        self.history = []

    def _current_payoff(self):
        if not self.agent_mode:
            T, R, P, S = self.base_T, self.base_R, self.base_P, self.base_S
        else:
            # Медиана предложений
            T = median([s.proposed_T for s in self.population])
            R = median([s.proposed_R for s in self.population])
            P = median([s.proposed_P for s in self.population])
            S = median([s.proposed_S for s in self.population])
            # Гарантируем T > R > P > S (иначе не дилемма)
            T = max(T, R + 0.1)
            R = max(R, P + 0.1)
            P = max(P, S + 0.1)

        return {
            ('C', 'C'): R, ('C', 'D'): S,
            ('D', 'C'): T, ('D', 'D'): P,
        }, T, R, P, S

    def step(self):
        payoff, T, R, P, S = self._current_payoff()
        n = len(self.population)
        scores = [0.0] * n
        n_opp = min(12, n - 1)

        for i in range(n):
            opponents = self.rng.sample([j for j in range(n) if j != i], n_opp)
            for j in opponents:
                s1, s2 = play_game(self.population[i], self.population[j],
                                   self.rounds, payoff)
                scores[i] += s1
                scores[j] += s2

        new_pop = []
        for _ in range(self.pop_size):
            i1, i2 = self.rng.sample(range(n), 2)
            winner = i1 if scores[i1] >= scores[i2] else i2
            child = mutate(self.population[winner], self.rng, self.max_states,
                          mutate_proposals=self.agent_mode)
            new_pop.append(child)

        self.population = new_pop
        self._record(T, R, P, S)

    def _record(self, T, R, P, S):
        n = len(self.population)
        avg_c = sum(s.complexity for s in self.population) / n
        first_c = sum(1 for s in self.population if s.actions[s.initial_state] == 'C')
        coop = first_c / n

        self.history.append({
            "avg_complexity": round(avg_c, 2),
            "coop_rate": round(coop, 2),
            "T": round(T, 2), "R": round(R, 2),
            "P": round(P, 2), "S": round(S, 2),
            "T_minus_S": round(T - S, 2),
        })

    def run(self, generations=400):
        payoff, T, R, P, S = self._current_payoff()
        self._record(T, R, P, S)
        for _ in range(generations):
            self.step()
        return self.history


def run_experiment():
    print("=" * 70)
    print("АДАПТАЦИЯ vs АГЕНТНОСТЬ")
    print("=" * 70)
    print("Adapters: эволюционируют стратегию, правила фиксированы")
    print("Agents: эволюционируют стратегию + голосуют за правила")
    print("Начальная матрица: T=7, R=3, P=1, S=-1 (высокие ставки)")

    n_seeds = 10

    # Эксперимент 1: Сравнение adapters vs agents
    print("\n\n--- Эксперимент 1: Adapters vs Agents (10 seeds) ---")

    adapter_coops, adapter_complexities = [], []
    agent_coops, agent_complexities = [], []
    agent_T_S, agent_final_T, agent_final_R, agent_final_P, agent_final_S = [], [], [], [], []

    for seed in range(n_seeds):
        # Adapters
        exp_a = AgencyExperiment(agent_mode=False, seed=seed)
        h_a = exp_a.run(400)
        late = h_a[-50:]
        adapter_coops.append(sum(r["coop_rate"] for r in late) / len(late))
        adapter_complexities.append(sum(r["avg_complexity"] for r in late) / len(late))

        # Agents
        exp_b = AgencyExperiment(agent_mode=True, seed=seed)
        h_b = exp_b.run(400)
        late = h_b[-50:]
        agent_coops.append(sum(r["coop_rate"] for r in late) / len(late))
        agent_complexities.append(sum(r["avg_complexity"] for r in late) / len(late))
        agent_T_S.append(sum(r["T_minus_S"] for r in late) / len(late))
        agent_final_T.append(late[-1]["T"])
        agent_final_R.append(late[-1]["R"])
        agent_final_P.append(late[-1]["P"])
        agent_final_S.append(late[-1]["S"])

    avg = lambda lst: sum(lst) / len(lst)

    print(f"\n  {'':>12} | {'cooperation':>12} | {'complexity':>11} | {'T-S':>6}")
    print("  " + "-" * 50)
    print(f"  {'Adapters':>12} | {avg(adapter_coops):>12.2f} | {avg(adapter_complexities):>11.2f} | {8.0:>6.1f}")
    print(f"  {'Agents':>12} | {avg(agent_coops):>12.2f} | {avg(agent_complexities):>11.2f} | {avg(agent_T_S):>6.1f}")

    delta_coop = avg(agent_coops) - avg(adapter_coops)
    delta_c = avg(agent_complexities) - avg(adapter_complexities)
    print(f"\n  Δcoop = {delta_coop:+.2f}")
    print(f"  Δcomplexity = {delta_c:+.2f}")

    # Какую матрицу выбрали агенты?
    print(f"\n  Матрица, выбранная агентами (median по seeds):")
    print(f"    T = {avg(agent_final_T):.2f} (было {7})")
    print(f"    R = {avg(agent_final_R):.2f} (было {3})")
    print(f"    P = {avg(agent_final_P):.2f} (было {1})")
    print(f"    S = {avg(agent_final_S):.2f} (было {-1})")
    print(f"    T-S = {avg(agent_T_S):.2f} (было {8})")

    # Эксперимент 2: Динамика — как агенты меняют правила
    print("\n\n--- Эксперимент 2: Динамика изменения правил (seed=0) ---")
    exp = AgencyExperiment(agent_mode=True, seed=0)
    h = exp.run(500)
    print(f"  {'gen':>4} | {'coop':>5} | {'cmplx':>5} | {'T':>5} {'R':>5} {'P':>5} {'S':>6} | {'T-S':>5}")
    print("  " + "-" * 55)
    for gen in [0, 25, 50, 100, 150, 200, 300, 400, 500]:
        if gen < len(h):
            r = h[gen]
            print(f"  {gen:>4} | {r['coop_rate']:>5.2f} | {r['avg_complexity']:>5.2f} | "
                  f"{r['T']:>5.1f} {r['R']:>5.1f} {r['P']:>5.1f} {r['S']:>6.2f} | {r['T_minus_S']:>5.1f}")

    # Эксперимент 3: Начинаем с низких ставок — что меняют агенты?
    print("\n\n--- Эксперимент 3: Начинаем с низких ставок (T=3.5, S=1) ---")
    low_T_S = []
    low_coops = []
    for seed in range(n_seeds):
        exp = AgencyExperiment(agent_mode=True, base_T=3.5, base_R=3, base_P=1, base_S=1, seed=seed)
        h = exp.run(400)
        late = h[-50:]
        low_coops.append(sum(r["coop_rate"] for r in late) / len(late))
        low_T_S.append(sum(r["T_minus_S"] for r in late) / len(late))

    print(f"  Начальные ставки: T-S=2.5")
    print(f"  Финальные ставки: T-S={avg(low_T_S):.2f}")
    print(f"  Кооперация: {avg(low_coops):.2f}")
    if avg(low_T_S) > 2.5 + 0.5:
        print(f"  → Агенты ПОВЫСИЛИ ставки (T-S: 2.5 → {avg(low_T_S):.1f})")
    elif avg(low_T_S) < 2.5 - 0.5:
        print(f"  → Агенты СНИЗИЛИ ставки (T-S: 2.5 → {avg(low_T_S):.1f})")
    else:
        print(f"  → Ставки примерно сохранились")

    # Итог
    print("\n\n" + "=" * 70)
    print("ИТОГ")
    print("=" * 70)

    if delta_coop > 0.05:
        print("  Агенты кооперируются БОЛЬШЕ, чем адаптеры.")
        if avg(agent_T_S) < 7:
            print(f"  КАК: снизили ставки (T-S: 8 → {avg(agent_T_S):.1f})")
            print("  Агенты *спроектировали себе более безопасный мир*.")
        else:
            print("  При сохранении высоких ставок.")
    elif delta_coop < -0.05:
        print("  Агенты кооперируются МЕНЬШЕ.")
        if avg(agent_T_S) > 8:
            print(f"  Агенты *повысили ставки* (T-S: 8 → {avg(agent_T_S):.1f})")
    else:
        print("  Разница в кооперации незначительна.")


if __name__ == "__main__":
    run_experiment()
