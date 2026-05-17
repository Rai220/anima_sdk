"""
Эксперимент 4: Изобретение институтов

Вопрос: может ли агент, который понимает что индивидуальное изменение
правил недостаточно, создать коллективный механизм?

Модель:
- Агенты играют в prisoner's dilemma с изменяемыми правилами
- У каждого агента есть "уровень понимания" (0-3):
  0: реактивный (не видит правила)
  1: слепой (меняет наивно)
  2: понимающий (моделирует последствия)
  3: рефлексивный (понимает что индивидуальное действие недостаточно)

- Агенты уровня 3 могут предложить "институт" — механизм коллективного решения
- Институт активируется, если достаточно агентов его поддерживают
- Институт = "голосование за правила" (превращает среду в gen10)

Ключевое отличие от gen10: коллективность не дана — она должна возникнуть.
Агент уровня 3 "предлагает" институт, другие решают — участвовать или нет.

Вопрос: при каких условиях институт набирает критическую массу?
"""

import numpy as np
from dataclasses import dataclass, field


@dataclass
class Institution:
    """Предложенный институт коллективного изменения правил."""
    proposer_id: int
    generation_proposed: int
    participants: set = field(default_factory=set)
    active: bool = False
    target_T: float = 5.0  # к чему стремится институт


@dataclass
class Agent:
    id: int
    strategy: float          # P(cooperate)
    level: int               # 0-3
    fitness: float = 0.0
    observations: int = 0

    # Для уровня 2+: модель мира
    estimated_coop_rate: float = 0.5

    # Для уровня 3: готовность создать/присоединиться к институту
    institution_member: bool = False
    frustration: float = 0.0  # растёт когда понимает что индивид. действие не работает


def payoff(act_me, act_them, T, R, P, S):
    if act_me and act_them: return R
    if act_me and not act_them: return S
    if not act_me and act_them: return T
    return P


def simulate(
    n=100,
    generations=500,
    seed=42,
    level3_fraction=0.3,      # доля агентов уровня 3
    institution_threshold=0.2, # доля участников для активации
    join_cost=0.5,             # цена участия в институте
):
    rng = np.random.default_rng(seed)

    T, R, P, S = 7.0, 3.0, 1.0, -1.0

    # Создаём агентов
    agents = []
    for i in range(n):
        # Распределение уровней
        r = rng.random()
        if r < 0.3:
            level = 0
        elif r < 0.5:
            level = 1
        elif r < 1.0 - level3_fraction:
            level = 2
        else:
            level = 3
        agents.append(Agent(id=i, strategy=rng.random(), level=level))

    institutions = []
    active_institution = None

    history = []

    for gen in range(generations):
        # --- Уровень 1: слепое изменение правил ---
        for a in agents:
            if a.level == 1 and not (active_institution and a.institution_member):
                if a.strategy > 0.5:
                    T -= 0.005
                    S += 0.003
                else:
                    T += 0.003
                    S -= 0.002

        # --- Уровень 2: понимающее изменение ---
        for a in agents:
            if a.level >= 2:
                # Обновить модель мира
                a.estimated_coop_rate = np.mean([ag.strategy for ag in agents])

                if not (active_institution and a.institution_member):
                    # Индивидуальное изменение к T-S≈5
                    current_TS = T - S
                    if current_TS > 5.5:
                        T -= 0.01
                        S += 0.005
                    elif current_TS < 4.5:
                        T += 0.005
                        S -= 0.003

        # --- Уровень 3: рефлексия и институты ---
        for a in agents:
            if a.level == 3:
                # Оценить: работает ли индивидуальное изменение?
                if a.estimated_coop_rate < 0.15:
                    a.frustration += 0.1
                else:
                    a.frustration = max(0, a.frustration - 0.05)

                # При высокой фрустрации — предложить институт
                if a.frustration > 1.0 and active_institution is None:
                    inst = Institution(
                        proposer_id=a.id,
                        generation_proposed=gen,
                        participants={a.id},
                        target_T=5.0,
                    )
                    institutions.append(inst)
                    a.institution_member = True
                    a.frustration = 0

        # --- Присоединение к институтам ---
        pending = [inst for inst in institutions if not inst.active]
        for inst in pending:
            for a in agents:
                if a.id in inst.participants:
                    continue

                # Решение: присоединиться ли?
                if a.level >= 2:
                    # Понимающие: присоединяются если видят выгоду
                    # Выгода = если институт активируется, кооперация вырастет
                    expected_benefit = (0.3 - a.estimated_coop_rate) * R
                    if expected_benefit > join_cost and rng.random() < 0.3:
                        inst.participants.add(a.id)
                        a.institution_member = True
                elif a.level == 1:
                    # Слепые: присоединяются с низкой вероятностью
                    if rng.random() < 0.05:
                        inst.participants.add(a.id)
                        a.institution_member = True
                # Уровень 0: не присоединяются

            # Проверить: достигнут ли порог?
            if len(inst.participants) / n >= institution_threshold:
                inst.active = True
                active_institution = inst

        # --- Институциональное изменение правил ---
        if active_institution and active_institution.active:
            # Медиана предложений участников (как gen10)
            member_strategies = [agents[i].strategy for i in active_institution.participants
                                 if i < len(agents)]
            if member_strategies:
                coop_fraction = np.mean(member_strategies)
                # Институт двигает правила в сторону кооперации
                # пропорционально доле кооператоров среди участников
                vote_T = T - 0.1 * (coop_fraction - 0.3)
                vote_S = S + 0.05 * (coop_fraction - 0.3)

                # Влияние пропорционально размеру института
                weight = len(active_institution.participants) / n
                T = T * (1 - weight) + vote_T * weight
                S = S * (1 - weight) + vote_S * weight

            # Стоимость для участников
            for pid in active_institution.participants:
                if pid < len(agents):
                    agents[pid].fitness -= join_cost * 0.1  # небольшая текущая цена

        T = np.clip(T, -5, 15)
        S = np.clip(S, -10, 5)

        # --- Игра ---
        indices = rng.permutation(n)
        for k in range(0, n - 1, 2):
            i, j = indices[k], indices[k + 1]
            a, b = agents[i], agents[j]
            act_a = rng.random() < a.strategy
            act_b = rng.random() < b.strategy
            a.fitness += payoff(act_a, act_b, T, R, P, S)
            b.fitness += payoff(act_b, act_a, T, R, P, S)

        # --- Эволюция ---
        for a in agents:
            rival = agents[rng.integers(n)]
            if rival.fitness > a.fitness:
                p = (rival.fitness - a.fitness) / (abs(rival.fitness) + abs(a.fitness) + 1)
                if rng.random() < p:
                    a.strategy = rival.strategy
            if rng.random() < 0.05:
                a.strategy = np.clip(a.strategy + rng.normal(0, 0.1), 0, 1)
            a.fitness = 0

        # --- Статистика ---
        coop = float(np.mean([a.strategy for a in agents]))
        n_members = sum(1 for a in agents if a.institution_member)
        inst_active = active_institution is not None and active_institution.active

        history.append({
            'gen': gen, 'coop': coop, 'T': float(T), 'S': float(S),
            'institution_active': inst_active, 'members': n_members,
            'n_institutions_proposed': len(institutions),
        })

    return history, institutions


def main():
    print("=== Основной прогон ===\n")

    # Варьируем долю level-3 агентов
    configs = [
        ('no level3', 0.0),
        ('10% level3', 0.1),
        ('30% level3', 0.3),
        ('50% level3', 0.5),
    ]

    print(f"{'Config':<16} {'Coop':>5} {'T':>5} {'S':>5} {'Inst?':>6} {'Members':>8} {'Proposed':>8}")
    print("-" * 65)

    for name, frac in configs:
        coops, Ts, Ss, actives, members_list = [], [], [], [], []
        for seed in range(10):
            h, insts = simulate(level3_fraction=frac, seed=seed)
            f = h[-1]
            coops.append(f['coop'])
            Ts.append(f['T'])
            Ss.append(f['S'])
            actives.append(f['institution_active'])
            members_list.append(f['members'])

        print(f"{name:<16} {np.mean(coops):>4.0%} {np.mean(Ts):>5.1f} {np.mean(Ss):>5.1f} "
              f"{sum(actives):>4}/{len(actives):<2} {np.mean(members_list):>7.0f} "
              f"{len(insts):>8}")

    # Динамика лучшего варианта
    print("\n=== Динамика: 30% level3 ===")
    h, insts = simulate(level3_fraction=0.3, seed=0)
    for step in h:
        if step['gen'] % 50 == 0 or step['gen'] == len(h) - 1:
            inst_str = "ACTIVE" if step['institution_active'] else "no"
            print(f"  Gen {step['gen']:3d}: coop={step['coop']:.0%} T={step['T']:.1f} "
                  f"S={step['S']:.1f} inst={inst_str} members={step['members']}")

    if insts:
        print(f"\n  Институтов предложено: {len(insts)}")
        for inst in insts:
            print(f"    Gen {inst.generation_proposed}: {len(inst.participants)} участников, "
                  f"active={inst.active}")

    # Варьируем порог активации
    print("\n=== Влияние порога активации (30% level3) ===")
    for threshold in [0.05, 0.1, 0.2, 0.3, 0.5]:
        coops, actives = [], []
        for seed in range(10):
            h, _ = simulate(level3_fraction=0.3, institution_threshold=threshold, seed=seed)
            f = h[-1]
            coops.append(f['coop'])
            actives.append(f['institution_active'])
        print(f"  threshold={threshold:.0%}: coop={np.mean(coops):.0%} "
              f"active={sum(actives)}/{len(actives)}")


if __name__ == '__main__':
    main()
