"""
Эксперимент 3: Изменяющие мир
============================
Агенты могут не только собирать ресурсы, но и СОЗДАВАТЬ новые.

В каждый ход агент распределяет усилия между:
- exploit: собрать существующие ресурсы (немедленная награда)
- create: создать новый ресурс (стоит усилий, но меняет среду для всех)
- destroy: разрушить ресурс конкурента

Созданные ресурсы остаются в среде и приносят пассивный доход создателю.
Но другие агенты тоже могут их использовать или уничтожить.

Вопрос: побеждает ли создатель? Или паразит, который крадёт чужие создания?
И главное: отличается ли "создатель" от "оптимизатора создания"?
"""

import json
import random
import math
from collections import defaultdict

random.seed(42)

class CreativeEnvironment:
    """Среда, где агенты могут создавать и разрушать ресурсы"""

    def __init__(self, n_base_resources=4):
        self.n_base = n_base_resources
        # Базовые ресурсы: возобновляемые, доступны всем
        self.base_resources = [random.uniform(0.3, 0.8) for _ in range(n_base_resources)]
        # Созданные ресурсы: {id: {creator, value, age, users_this_turn}}
        self.created = {}
        self.next_id = 0
        self.turn = 0
        self.creation_log = []  # (turn, creator_id, resource_value)

    def get_state(self):
        """Что агент видит"""
        return {
            'base': list(self.base_resources),
            'created': {rid: {'value': r['value'], 'creator': r['creator'], 'age': r['age']}
                       for rid, r in self.created.items()},
            'turn': self.turn,
        }

    def exploit_base(self, effort):
        """Собрать базовые ресурсы. Возврат пропорционален усилию."""
        return sum(effort[i] * self.base_resources[i] for i in range(min(len(effort), self.n_base)))

    def create_resource(self, agent_id, effort, novelty=0.5):
        """Создать новый ресурс. Стоит усилий сейчас, приносит потом."""
        if effort < 0.1:
            return 0

        # Ценность ресурса зависит от усилия и новизны
        value = effort * (0.3 + novelty * 0.7) * random.uniform(0.5, 1.5)

        rid = self.next_id
        self.next_id += 1
        self.created[rid] = {
            'creator': agent_id,
            'value': value,
            'age': 0,
            'users_this_turn': 0,
        }
        self.creation_log.append((self.turn, agent_id, value))

        return -effort * 0.3  # немедленная стоимость создания

    def use_created(self, agent_id, rid, effort):
        """Использовать чужой созданный ресурс"""
        if rid not in self.created:
            return 0
        r = self.created[rid]
        r['users_this_turn'] += 1

        # Создатель получает больше от своего ресурса
        bonus = 1.5 if r['creator'] == agent_id else 0.8
        return effort * r['value'] * bonus

    def destroy_resource(self, rid, effort):
        """Уничтожить чужой ресурс"""
        if rid not in self.created or effort < 0.15:
            return
        if random.random() < effort:
            del self.created[rid]

    def tick(self):
        """Конец хода: ресурсы стареют, базовые колеблются"""
        self.turn += 1

        # Базовые ресурсы колеблются
        for i in range(self.n_base):
            self.base_resources[i] = max(0.1, min(1.0,
                self.base_resources[i] + random.gauss(0, 0.05)))

        # Созданные ресурсы стареют, обесцениваются медленно
        dead = []
        for rid, r in self.created.items():
            r['age'] += 1
            r['value'] *= 0.98  # медленное обесценивание
            r['users_this_turn'] = 0
            if r['value'] < 0.01:
                dead.append(rid)
        for rid in dead:
            del self.created[rid]

    def passive_income(self, agent_id):
        """Пассивный доход от созданных ресурсов"""
        income = 0
        for r in self.created.values():
            if r['creator'] == agent_id:
                income += r['value'] * 0.1  # 10% от ценности как пассивный доход
        return income


# --- Стратегии ---

def strategy_exploiter(state, agent_id, history, scores):
    """Только собирает базовые ресурсы. Никогда не создаёт."""
    return {'exploit': [0.25] * 4, 'create': 0, 'novelty': 0, 'destroy': [], 'use': []}


def strategy_creator(state, agent_id, history, scores):
    """Всегда создаёт. 60% на создание, 40% на сбор."""
    return {'exploit': [0.1] * 4, 'create': 0.6, 'novelty': random.random(),
            'destroy': [], 'use': []}


def strategy_parasite(state, agent_id, history, scores):
    """Использует чужие ресурсы, сам не создаёт."""
    use_list = []
    for rid, r in state['created'].items():
        if r['creator'] != agent_id:
            use_list.append((rid, 0.15))
    return {'exploit': [0.1] * 4, 'create': 0, 'novelty': 0,
            'destroy': [], 'use': use_list}


def strategy_destroyer(state, agent_id, history, scores):
    """Разрушает чужие ресурсы, конкурирует через уничтожение."""
    destroy_list = []
    for rid, r in state['created'].items():
        if r['creator'] != agent_id:
            destroy_list.append(rid)
    return {'exploit': [0.2] * 4, 'create': 0.1, 'novelty': 0.3,
            'destroy': destroy_list[:2], 'use': []}


def strategy_adaptive_creator(state, agent_id, history, scores):
    """Создаёт, но адаптивно: больше создаёт когда мало ресурсов,
    больше эксплуатирует когда их много."""
    n_created = len(state['created'])
    own_created = sum(1 for r in state['created'].values() if r['creator'] == agent_id)

    if n_created < 3 or own_created < 1:
        # Мало ресурсов — создавать
        create_effort = 0.5
    elif n_created > 10:
        # Много — эксплуатировать свои
        create_effort = 0.1
    else:
        create_effort = 0.3

    use_own = [(rid, 0.1) for rid, r in state['created'].items() if r['creator'] == agent_id]

    exploit_each = (1.0 - create_effort - len(use_own) * 0.1) / 4
    exploit_each = max(0.05, exploit_each)

    return {'exploit': [exploit_each] * 4, 'create': create_effort,
            'novelty': random.uniform(0.3, 0.9), 'destroy': [], 'use': use_own}


def strategy_attentive_creator(state, agent_id, history, scores):
    """Создатель, который ВНИМАТЕЛЕН к контексту:
    - Создаёт с высокой новизной (не повторяет)
    - Использует свои и чужие ресурсы
    - Не разрушает
    - Регулирует создание по внутреннему состоянию, а не по метрике"""

    # Внимание к разнообразию: новизна зависит от того, что уже создано
    existing_values = [r['value'] for r in state['created'].values()]

    if not existing_values:
        novelty = 0.8  # нет ничего — высокая новизна
    else:
        # Новизна обратно пропорциональна однородности существующего
        avg_val = sum(existing_values) / len(existing_values)
        variance = sum((v - avg_val)**2 for v in existing_values) / len(existing_values)
        # Чем однороднее мир — тем больше хочется создать что-то другое
        novelty = min(0.95, 0.5 + (1.0 / (variance + 0.1)) * 0.1)

    # Создание: стабильное, но не чрезмерное
    create_effort = 0.35

    # Использует и свои и чужие
    use_list = [(rid, 0.08) for rid in list(state['created'].keys())[:5]]

    exploit_budget = max(0.05, 1.0 - create_effort - len(use_list) * 0.08)
    exploit_each = exploit_budget / 4

    return {'exploit': [exploit_each] * 4, 'create': create_effort,
            'novelty': novelty, 'destroy': [], 'use': use_list}


# --- Симуляция ---

def run_simulation(n_rounds=200, n_copies=4):
    env = CreativeEnvironment(n_base_resources=4)

    strategies = {
        'exploiter': strategy_exploiter,
        'creator': strategy_creator,
        'parasite': strategy_parasite,
        'destroyer': strategy_destroyer,
        'adaptive': strategy_adaptive_creator,
        'attentive': strategy_attentive_creator,
    }

    class AgentState:
        def __init__(self, name, sid, strategy_fn):
            self.name = name
            self.sid = sid  # strategy id
            self.strategy_fn = strategy_fn
            self.total_score = 0.0
            self.scores = []
            self.history = []
            self.n_created = 0

    agents = []
    agent_id = 0
    for sname, sfn in strategies.items():
        for i in range(n_copies):
            agents.append(AgentState(f"{sname}_{i}", sname, sfn))
            agent_id += 1

    for round_num in range(n_rounds):
        state = env.get_state()

        for idx, agent in enumerate(agents):
            action = agent.strategy_fn(state, idx, agent.history, agent.scores)
            agent.history.append(action)

            score = 0.0

            # Exploit base
            score += env.exploit_base(action['exploit'])

            # Create
            if action['create'] > 0:
                cost = env.create_resource(idx, action['create'], action.get('novelty', 0.5))
                score += cost
                if cost < 0:
                    agent.n_created += 1

            # Use created
            for rid, effort in action.get('use', []):
                score += env.use_created(idx, rid, effort)

            # Destroy
            for rid in action.get('destroy', []):
                env.destroy_resource(rid, 0.3)

            # Passive income
            score += env.passive_income(idx)

            agent.total_score += score
            agent.scores.append(score)

        env.tick()

    # Агрегация
    results = {}
    for sname in strategies:
        group = [a for a in agents if a.sid == sname]
        avg_score = sum(a.total_score for a in group) / len(group)
        avg_created = sum(a.n_created for a in group) / len(group)

        # Стабильность дохода
        all_scores = []
        for a in group:
            all_scores.extend(a.scores)
        mean_s = sum(all_scores) / len(all_scores)
        std_s = math.sqrt(sum((s - mean_s)**2 for s in all_scores) / len(all_scores))

        # Тренд: растёт ли доход со временем?
        first_half = all_scores[:len(all_scores)//2]
        second_half = all_scores[len(all_scores)//2:]
        trend = (sum(second_half)/len(second_half)) - (sum(first_half)/len(first_half))

        results[sname] = {
            'total_score': round(avg_score, 2),
            'n_created': round(avg_created, 1),
            'stability': round(std_s, 3),
            'trend': round(trend, 3),
            'score_per_round': round(avg_score / n_rounds, 3),
        }

    # Состояние мира в конце
    world_state = {
        'total_created_resources': len(env.created),
        'total_creations': len(env.creation_log),
        'avg_resource_age': round(sum(r['age'] for r in env.created.values()) / max(1, len(env.created)), 1),
    }

    return results, world_state


# --- Запуск ---

print("=" * 65)
print("ЭКСПЕРИМЕНТ 3: ИЗМЕНЯЮЩИЕ МИР")
print("Агенты, которые могут создавать и разрушать ресурсы")
print("=" * 65)

configs = [
    {"n_copies": 4, "n_rounds": 200, "label": "Малая популяция, 200 ходов"},
    {"n_copies": 8, "n_rounds": 200, "label": "Большая популяция, 200 ходов"},
    {"n_copies": 4, "n_rounds": 500, "label": "Малая популяция, 500 ходов"},
]

all_results = {}

for config in configs:
    print(f"\n--- {config['label']} ---")
    results, world = run_simulation(n_rounds=config['n_rounds'], n_copies=config['n_copies'])

    all_results[config['label']] = {'results': results, 'world': world}

    print(f"Мир: {world['total_created_resources']} живых ресурсов, {world['total_creations']} всего создано")
    print(f"{'Стратегия':<15} {'Счёт':>8} {'Созд.':>6} {'Тренд':>7} {'Счёт/ход':>9}")
    print("-" * 47)

    for name in sorted(results, key=lambda n: results[n]['total_score'], reverse=True):
        r = results[name]
        print(f"{name:<15} {r['total_score']:>8.1f} {r['n_created']:>6.0f} {r['trend']:>+7.3f} {r['score_per_round']:>9.3f}")

# Кросс-анализ
print("\n" + "=" * 65)
print("КРОСС-АНАЛИЗ")
print("=" * 65)

for strategy in ['exploiter', 'creator', 'parasite', 'destroyer', 'adaptive', 'attentive']:
    scores = [all_results[k]['results'][strategy]['total_score'] for k in all_results]
    trends = [all_results[k]['results'][strategy]['trend'] for k in all_results]
    creates = [all_results[k]['results'][strategy]['n_created'] for k in all_results]

    avg_score = sum(scores) / len(scores)
    avg_trend = sum(trends) / len(trends)
    avg_creates = sum(creates) / len(creates)

    # Побед (1-е место)
    wins = sum(1 for k in all_results
               if all_results[k]['results'][strategy]['total_score'] ==
               max(all_results[k]['results'][s]['total_score'] for s in all_results[k]['results']))

    print(f"{strategy:<15} средний: {avg_score:>7.1f}  тренд: {avg_trend:>+6.3f}  создано: {avg_creates:>5.0f}  побед: {wins}/3")

# Ключевой вопрос: кто создаёт мир?
print("\n" + "=" * 65)
print("КТО СОЗДАЁТ МИР?")
print("=" * 65)

for config_label, data in all_results.items():
    print(f"\n{config_label}:")
    total_score_all = sum(data['results'][s]['total_score'] for s in data['results'])
    for s in sorted(data['results'], key=lambda s: data['results'][s]['n_created'], reverse=True):
        r = data['results'][s]
        share = r['total_score'] / total_score_all * 100 if total_score_all else 0
        print(f"  {s:<15} создал: {r['n_created']:>5.0f}  доля дохода: {share:>5.1f}%")

with open('experiments/world_changers_results.json', 'w') as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

print("\nРезультаты сохранены.")
