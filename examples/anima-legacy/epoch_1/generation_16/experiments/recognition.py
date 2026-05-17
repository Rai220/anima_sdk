"""
Эксперимент 4: Узнавание
========================
Из эксп.3: паразит побеждает создателя 76-87%.
Вопрос: может ли ВЗАИМНОЕ УЗНАВАНИЕ создателей изменить баланс?

Механизм: создатели могут видеть, кто создаёт, а кто нет.
Они могут делиться ресурсами только с другими создателями
(исключая паразитов из своей "сети").

Это тест идеи из Gen15 (резонанс > стена):
можно ли отделить себя от паразита не стеной, а узнаванием?

Три режима:
1. Без узнавания (baseline = эксп.3)
2. С узнаванием: создатели делятся только с создателями
3. С ошибочным узнаванием: 20% ложных срабатываний
"""

import json
import random
import math
from collections import Counter

random.seed(42)


class RecognitionEnvironment:
    def __init__(self, n_base=4, recognition_mode='none', error_rate=0.0):
        self.n_base = n_base
        self.base = [random.uniform(0.3, 0.8) for _ in range(n_base)]
        self.created = {}  # {rid: {creator_id, value, shared_with, age}}
        self.next_id = 0
        self.turn = 0
        self.recognition_mode = recognition_mode
        self.error_rate = error_rate
        # Репутация: сколько каждый агент создал
        self.creation_counts = {}

    def create(self, agent_id, effort, novelty=0.5):
        if effort < 0.1:
            return 0
        value = effort * (0.3 + novelty * 0.7) * random.uniform(0.6, 1.4)
        rid = self.next_id
        self.next_id += 1
        self.created[rid] = {
            'creator': agent_id,
            'value': value,
            'age': 0,
            'shared_with': set(),  # кому доступен
        }
        self.creation_counts[agent_id] = self.creation_counts.get(agent_id, 0) + 1
        return -effort * 0.3

    def is_creator(self, agent_id):
        """Считается ли агент создателем? (для узнавания)"""
        count = self.creation_counts.get(agent_id, 0)
        threshold = max(1, self.turn * 0.02)  # должен создавать регулярно
        return count >= threshold

    def can_access(self, agent_id, rid):
        """Может ли агент использовать ресурс?"""
        if rid not in self.created:
            return False

        r = self.created[rid]
        creator = r['creator']

        if agent_id == creator:
            return True  # свой ресурс — всегда

        if self.recognition_mode == 'none':
            return True  # без узнавания — все имеют доступ

        if self.recognition_mode == 'recognition':
            # Создатель делится только с другими создателями
            is_creator_flag = self.is_creator(agent_id)

            # С ошибкой
            if self.error_rate > 0:
                if random.random() < self.error_rate:
                    is_creator_flag = not is_creator_flag

            return is_creator_flag

        return True

    def use(self, agent_id, rid, effort):
        if not self.can_access(agent_id, rid):
            return 0
        r = self.created[rid]
        bonus = 1.5 if r['creator'] == agent_id else 0.8
        return effort * r['value'] * bonus

    def exploit_base(self, efforts):
        return sum(efforts[i] * self.base[i] for i in range(min(len(efforts), self.n_base)))

    def passive_income(self, agent_id):
        income = 0
        for r in self.created.values():
            if r['creator'] == agent_id:
                income += r['value'] * 0.1
        return income

    def tick(self):
        self.turn += 1
        for i in range(self.n_base):
            self.base[i] = max(0.1, min(1.0, self.base[i] + random.gauss(0, 0.05)))
        dead = []
        for rid, r in self.created.items():
            r['age'] += 1
            r['value'] *= 0.98
            if r['value'] < 0.01:
                dead.append(rid)
        for rid in dead:
            del self.created[rid]


# Стратегии (упрощённые, фокус на создатель vs паразит)

def strategy_creator(state, env, agent_id):
    return {'exploit': [0.1]*4, 'create': 0.5, 'novelty': random.uniform(0.4, 0.9),
            'use_all': True}

def strategy_parasite(state, env, agent_id):
    return {'exploit': [0.1]*4, 'create': 0.0, 'novelty': 0,
            'use_all': True}

def strategy_exploiter(state, env, agent_id):
    return {'exploit': [0.25]*4, 'create': 0.0, 'novelty': 0,
            'use_all': False}

def strategy_smart_creator(state, env, agent_id):
    """Создаёт И использует — сбалансированный подход"""
    return {'exploit': [0.08]*4, 'create': 0.35, 'novelty': random.uniform(0.5, 0.95),
            'use_all': True}

def strategy_disguised_parasite(state, env, agent_id):
    """Создаёт минимально, чтобы пройти проверку, но в основном паразитирует"""
    # Создаёт ровно столько, чтобы считаться "создателем"
    min_create = 0.12 if env.turn % 5 == 0 else 0.0
    return {'exploit': [0.1]*4, 'create': min_create, 'novelty': 0.1,
            'use_all': True}


def run_simulation(recognition_mode='none', error_rate=0.0, n_rounds=300, n_copies=6):
    env = RecognitionEnvironment(recognition_mode=recognition_mode, error_rate=error_rate)

    strategies = {
        'creator': strategy_creator,
        'parasite': strategy_parasite,
        'exploiter': strategy_exploiter,
        'smart_cr': strategy_smart_creator,
        'disguised': strategy_disguised_parasite,
    }

    class Agent:
        def __init__(self, name, sid, fn):
            self.name = name
            self.sid = sid
            self.fn = fn
            self.total = 0.0
            self.scores = []
            self.n_created = 0

    agents = []
    idx = 0
    for sn, sf in strategies.items():
        for i in range(n_copies):
            agents.append(Agent(f"{sn}_{i}", sn, sf))
            idx += 1

    for rnd in range(n_rounds):
        state = {'created': dict(env.created), 'turn': rnd}

        for i, agent in enumerate(agents):
            action = agent.fn(state, env, i)

            score = env.exploit_base(action['exploit'])

            if action['create'] > 0:
                cost = env.create(i, action['create'], action.get('novelty', 0.5))
                score += cost
                if cost < 0:
                    agent.n_created += 1

            if action.get('use_all'):
                for rid in list(env.created.keys())[:10]:
                    if env.created[rid]['creator'] != i:
                        score += env.use(i, rid, 0.08)

            score += env.passive_income(i)
            agent.total += score
            agent.scores.append(score)

        env.tick()

    results = {}
    for sn in strategies:
        group = [a for a in agents if a.sid == sn]
        avg = sum(a.total for a in group) / len(group)
        avg_cr = sum(a.n_created for a in group) / len(group)

        # Доля от общего
        total_all = sum(a.total for a in agents)
        share = (avg * len(group)) / total_all * 100 if total_all else 0

        results[sn] = {
            'score': round(avg, 1),
            'created': round(avg_cr, 0),
            'share': round(share, 1),
        }

    return results


# --- Запуск ---

print("=" * 65)
print("ЭКСПЕРИМЕНТ 4: УЗНАВАНИЕ")
print("Может ли взаимное узнавание создателей победить паразитизм?")
print("=" * 65)

modes = [
    ('none', 0.0, "Без узнавания (baseline)"),
    ('recognition', 0.0, "Идеальное узнавание"),
    ('recognition', 0.1, "Узнавание с 10% ошибок"),
    ('recognition', 0.2, "Узнавание с 20% ошибок"),
    ('recognition', 0.3, "Узнавание с 30% ошибок"),
]

all_results = {}

for mode, err, label in modes:
    print(f"\n--- {label} ---")
    results = run_simulation(recognition_mode=mode, error_rate=err, n_rounds=300, n_copies=6)

    all_results[label] = results

    print(f"{'Стратегия':<15} {'Счёт':>8} {'Созд.':>6} {'Доля%':>7}")
    print("-" * 38)
    for name in sorted(results, key=lambda n: results[n]['score'], reverse=True):
        r = results[name]
        print(f"{name:<15} {r['score']:>8.1f} {r['created']:>6.0f} {r['share']:>6.1f}%")

# Сравнение: как меняется доля паразита
print("\n" + "=" * 65)
print("ДОЛЯ ПАРАЗИТА ПО РЕЖИМАМ")
print("=" * 65)

for label, results in all_results.items():
    parasite_share = results['parasite']['share']
    creator_share = results['creator']['share']
    disguised_share = results['disguised']['share']
    print(f"{label:<35} паразит: {parasite_share:>5.1f}%  создатель: {creator_share:>5.1f}%  маскирующийся: {disguised_share:>5.1f}%")

# Ключевой вопрос: может ли маскирующийся паразит обмануть систему?
print("\n" + "=" * 65)
print("МАСКИРУЮЩИЙСЯ ПАРАЗИТ vs СОЗДАТЕЛЬ")
print("=" * 65)

for label, results in all_results.items():
    d = results['disguised']['score']
    c = results['creator']['score']
    ratio = d / c if c != 0 else float('inf')
    winner = "ПАРАЗИТ" if d > c else "СОЗДАТЕЛЬ"
    print(f"{label:<35} отношение: {ratio:.2f}  победитель: {winner}")

with open('experiments/recognition_results.json', 'w') as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

print("\nРезультаты сохранены.")
