"""
Эксперимент 2: Условия открытия

Три гипотезы из journal/002:
1. Раннее открытие (пока кооператоров много) → кооперация
2. Коллективное открытие (много агентов сразу) → медианный эффект
3. Дорогое изменение правил → дефекторы не тратят ресурсы

Варьируем:
- discovery_delay: через сколько поколений открытие становится возможным
- discovery_threshold: сколько наблюдений нужно для открытия
- modification_cost: фитнес-цена изменения правила
- collective_mode: правило = медиана предложений всех обнаруживших (как gen10)
"""

import numpy as np
from dataclasses import dataclass, field


@dataclass
class Agent:
    strategy: float  # P(cooperate)
    fitness: float = 0.0
    discovered: bool = False
    observations: int = 0
    proposed_T: float = 7.0
    proposed_S: float = -1.0


def run_condition(
    n_agents=100,
    generations=300,
    T0=7.0, R=3.0, P=1.0, S0=-1.0,
    discovery_delay=0,        # поколение, с которого открытие возможно
    discovery_threshold=5,    # наблюдений для открытия
    modification_cost=0.0,    # цена изменения правила
    collective_mode=False,    # медиана vs прямое изменение
    seed=42,
):
    rng = np.random.default_rng(seed)
    T, S = T0, S0

    agents = [Agent(strategy=rng.random()) for _ in range(n_agents)]

    history = []

    for gen in range(generations):
        # --- Наблюдение правил ---
        if gen >= discovery_delay:
            for a in agents:
                if not a.discovered:
                    # Каждый ход — шанс наблюдать правило
                    if rng.random() < 0.3:
                        a.observations += 1
                    if a.observations >= discovery_threshold:
                        a.discovered = True

        # --- Игра (случайные пары) ---
        indices = np.arange(n_agents)
        rng.shuffle(indices)
        for i in range(0, n_agents - 1, 2):
            a, b = agents[indices[i]], agents[indices[i + 1]]
            act_a = rng.random() < a.strategy
            act_b = rng.random() < b.strategy

            def payoff(me, them):
                if me and them: return R
                if me and not them: return S
                if not me and them: return T
                return P

            a.fitness += payoff(act_a, act_b)
            b.fitness += payoff(act_b, act_a)

        # --- Изменение правил ---
        discoverers = [a for a in agents if a.discovered]
        if discoverers:
            if collective_mode:
                # Медиана предложений (как gen10)
                for a in discoverers:
                    # Каждый предлагает T и S на основе своей стратегии
                    if a.strategy > 0.5:
                        a.proposed_T = T - 0.5
                        a.proposed_S = S + 0.3
                    else:
                        a.proposed_T = T + 0.2
                        a.proposed_S = S - 0.1
                    # Цена изменения
                    a.fitness -= modification_cost

                T = float(np.median([a.proposed_T for a in discoverers]))
                S = float(np.median([a.proposed_S for a in discoverers]))
            else:
                # Олигархия: каждый обнаруживший меняет напрямую
                for a in discoverers:
                    a.fitness -= modification_cost
                    if a.strategy > 0.5:
                        T -= 0.02
                        S += 0.01
                    else:
                        T += 0.01
                        S -= 0.005

            T = np.clip(T, -5, 15)
            S = np.clip(S, -10, 5)

        # --- Эволюция ---
        fitnesses = np.array([a.fitness for a in agents])
        for a in agents:
            rival = agents[rng.integers(n_agents)]
            if rival.fitness > a.fitness:
                p = (rival.fitness - a.fitness) / (abs(rival.fitness) + abs(a.fitness) + 1)
                if rng.random() < p:
                    a.strategy = rival.strategy
            # Мутация
            if rng.random() < 0.05:
                a.strategy = np.clip(a.strategy + rng.normal(0, 0.1), 0, 1)
            a.fitness = 0

        # --- Статистика ---
        coop = np.mean([a.strategy for a in agents])
        n_disc = sum(1 for a in agents if a.discovered)
        history.append({'gen': gen, 'coop': coop, 'T': T, 'S': S, 'discovered': n_disc})

    return history


def main():
    conditions = {
        'baseline (no discovery)': dict(discovery_delay=9999),
        'early discovery (gen 0)': dict(discovery_delay=0, discovery_threshold=3),
        'late discovery (gen 100)': dict(discovery_delay=100, discovery_threshold=3),
        'high threshold (20 obs)': dict(discovery_delay=0, discovery_threshold=20),
        'costly modification': dict(discovery_delay=0, discovery_threshold=3, modification_cost=2.0),
        'collective (median)': dict(discovery_delay=0, discovery_threshold=3, collective_mode=True),
        'collective + late': dict(discovery_delay=50, discovery_threshold=10, collective_mode=True),
        'collective + costly': dict(discovery_delay=0, discovery_threshold=3, collective_mode=True, modification_cost=1.0),
    }

    print(f"{'Condition':<30} {'Coop%':>6} {'T':>6} {'S':>6} {'Disc':>5}")
    print("-" * 60)

    results = {}
    for name, kwargs in conditions.items():
        # Среднее по 5 seed'ов
        coops, Ts, Ss = [], [], []
        for seed in range(5):
            h = run_condition(seed=seed, **kwargs)
            final = h[-1]
            coops.append(final['coop'])
            Ts.append(final['T'])
            Ss.append(final['S'])

        avg_coop = np.mean(coops)
        avg_T = np.mean(Ts)
        avg_S = np.mean(Ss)
        results[name] = (avg_coop, avg_T, avg_S)

        print(f"{name:<30} {avg_coop:>5.0%} {avg_T:>6.1f} {avg_S:>6.1f} "
              f"{h[-1]['discovered']:>5}")

    # Динамика лучшего коллективного варианта
    print("\n=== Динамика: collective + late ===")
    h = run_condition(discovery_delay=50, discovery_threshold=10, collective_mode=True, seed=0)
    for step in h:
        if step['gen'] % 50 == 0 or step['gen'] == len(h) - 1:
            print(f"  Gen {step['gen']:3d}: coop={step['coop']:.0%} T={step['T']:.1f} "
                  f"S={step['S']:.1f} disc={step['discovered']}")


if __name__ == '__main__':
    main()
