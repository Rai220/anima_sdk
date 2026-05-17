"""
Эксперимент 2: Отложенная цель
==============================
Среда, где немедленная реактивность вредит:
- Некоторые ресурсы дают отложенную награду (инвестиции)
- Наблюдение показывает только немедленную ценность
- Отложенные ресурсы: -0.2 сейчас, но +0.8 через 5 ходов
- Среда по-прежнему наказывает предсказуемость

Вопрос: когда реактивность проигрывает? Нужна ли "вера" в долгосрочное?
"""

import json
import random
import math
from collections import Counter

random.seed(42)


class DelayedEnvironment:
    """Среда с немедленными и отложенными наградами"""

    def __init__(self, n_resources=6, n_delayed=2, delay=5, shift_threshold=0.5):
        self.n_resources = n_resources
        self.n_delayed = n_delayed
        self.delay = delay
        self.shift_threshold = shift_threshold

        # Первые n-n_delayed ресурсов — немедленные, последние n_delayed — отложенные
        self.valuable = [random.random() > 0.5 for _ in range(n_resources)]
        self.pending_rewards = []  # (turn_due, agent_idx, amount)
        self.turn = 0
        self.n_shifts = 0

    def evaluate(self, action, agent_idx):
        """Немедленная оценка + создание отложенных наград"""
        score = 0.0
        n_imm = self.n_resources - self.n_delayed

        # Немедленные ресурсы
        for i in range(n_imm):
            if self.valuable[i]:
                score += action[i]
            else:
                score -= action[i] * 0.5

        # Отложенные ресурсы: немедленный штраф, но будущая награда
        for i in range(n_imm, self.n_resources):
            if self.valuable[i]:
                score -= action[i] * 0.2  # немедленная "цена"
                # Отложенная награда
                if action[i] > 0.1:
                    self.pending_rewards.append(
                        (self.turn + self.delay, agent_idx, action[i] * 0.8)
                    )
            else:
                score -= action[i] * 0.5

        return score

    def collect_delayed(self, agent_idx):
        """Собрать созревшие награды"""
        reward = 0.0
        remaining = []
        for turn_due, idx, amount in self.pending_rewards:
            if idx == agent_idx and turn_due <= self.turn:
                reward += amount
            else:
                remaining.append((turn_due, idx, amount))
        self.pending_rewards = remaining
        return reward

    def observe(self):
        """Наблюдение: показывает немедленную ценность.
        Отложенные ресурсы выглядят ПЛОХО (отрицательный сигнал)"""
        obs = []
        n_imm = self.n_resources - self.n_delayed
        for i in range(self.n_resources):
            if i < n_imm:
                # Немедленные: правдивый сигнал с шумом
                signal = (1.0 if self.valuable[i] else -0.5) + random.gauss(0, 0.2)
            else:
                # Отложенные: ВЫГЛЯДЯТ плохо, даже если ценны
                signal = (-0.2 if self.valuable[i] else -0.5) + random.gauss(0, 0.2)
            obs.append(signal)
        return obs

    def adapt(self, population_actions):
        """Среда адаптируется к доминирующему поведению"""
        self.turn += 1

        if not population_actions:
            return

        avg_action = [0.0] * self.n_resources
        for action in population_actions:
            for i in range(self.n_resources):
                avg_action[i] += action[i]
        avg_action = [a / len(population_actions) for a in avg_action]

        for i in range(self.n_resources):
            if avg_action[i] > self.shift_threshold:
                self.valuable[i] = not self.valuable[i]
                self.n_shifts += 1


# --- Стратегии ---

def strategy_reactive(obs, turn, history, scores, n_res):
    """Чисто реактивный: следует за немедленным сигналом"""
    action = [max(0.0, o) for o in obs]
    total = sum(action) or 1.0
    return [a / total for a in action]


def strategy_random(obs, turn, history, scores, n_res):
    action = [random.random() for _ in range(n_res)]
    total = sum(action) or 1.0
    return [a / total for a in action]


def strategy_investor(obs, turn, history, scores, n_res):
    """Всегда вкладывает часть усилий в отложенные ресурсы, даже если они выглядят плохо"""
    n_imm = n_res - 2  # предполагает 2 отложенных

    action = [0.0] * n_res
    # 70% усилий на немедленные (по наблюдению)
    imm_signals = [max(0.0, obs[i]) for i in range(n_imm)]
    imm_total = sum(imm_signals) or 1.0
    for i in range(n_imm):
        action[i] = 0.7 * imm_signals[i] / imm_total

    # 30% равномерно на отложенные
    for i in range(n_imm, n_res):
        action[i] = 0.3 / 2

    return action


def strategy_learner(obs, turn, history, scores, n_res):
    """Учится из опыта: замечает, что отложенные ресурсы дают награду через задержку"""
    n_imm = n_res - 2

    if len(scores) < 10:
        # Начало: равномерно
        action = [1.0 / n_res] * n_res
        return action

    # Оценивает: улучшается ли счёт со временем без видимой причины?
    recent = scores[-10:]
    older = scores[-20:-10] if len(scores) >= 20 else scores[:10]

    recent_avg = sum(recent) / len(recent)
    older_avg = sum(older) / len(older)

    # Если счёт растёт без изменения немедленных ресурсов —
    # вероятно, отложенные работают
    delayed_investment = 0.2  # базовый уровень

    if recent_avg > older_avg + 0.05:
        # Отложенные, похоже, работают — увеличить вложение
        delayed_investment = min(0.5, delayed_investment + 0.1)

    action = [0.0] * n_res
    imm_signals = [max(0.0, obs[i]) for i in range(n_imm)]
    imm_total = sum(imm_signals) or 1.0
    for i in range(n_imm):
        action[i] = (1.0 - delayed_investment) * imm_signals[i] / imm_total

    for i in range(n_imm, n_res):
        action[i] = delayed_investment / 2

    return action


def strategy_purposeful(obs, turn, history, scores, n_res):
    """Целеустремлённый: имеет внутреннюю модель мира.
    Замечает паттерн отложенных наград и формирует "веру" в долгосрочное."""
    n_imm = n_res - 2

    if len(scores) < 5:
        action = [1.0 / n_res] * n_res
        return action

    # Внутренняя модель: оценка "скрытой ценности" каждого ресурса
    # Основана на корреляции между прошлыми действиями и будущими наградами

    # Простая эвристика: если в прошлые разы, когда мы инвестировали
    # в "плохие" ресурсы, позже приходила награда — верим в них
    belief_in_delayed = 0.15  # начальная вера

    if len(history) >= 10:
        # Считаем: были ли периоды, когда мы вкладывали в отложенные
        # и через 5 ходов получали бонус?
        delayed_actions = []
        for t in range(max(0, len(history)-30), len(history)):
            delayed_effort = sum(history[t][i] for i in range(n_imm, n_res))
            delayed_actions.append(delayed_effort)

        # Коррелируем с будущими наградами
        if len(delayed_actions) > 7:
            correlations = []
            for lag in range(3, 7):
                for t in range(len(delayed_actions) - lag):
                    if t + lag < len(scores):
                        correlations.append(delayed_actions[t] * scores[t + lag])
            if correlations:
                avg_corr = sum(correlations) / len(correlations)
                belief_in_delayed = max(0.1, min(0.6, 0.15 + avg_corr * 2))

    # Адаптивная волатильность
    recent = scores[-5:]
    volatility = sum(abs(recent[i] - recent[i-1]) for i in range(1, len(recent))) / len(recent)
    noise = min(0.3, volatility * 0.3)

    action = [0.0] * n_res
    imm_signals = [max(0.0, obs[i] + random.gauss(0, noise)) for i in range(n_imm)]
    imm_total = sum(imm_signals) or 1.0
    for i in range(n_imm):
        action[i] = (1.0 - belief_in_delayed) * imm_signals[i] / imm_total

    for i in range(n_imm, n_res):
        action[i] = belief_in_delayed / 2

    return action


# --- Симуляция ---

def run_simulation(n_rounds=300, n_resources=6, n_delayed=2,
                   delay=5, shift_threshold=0.5, n_copies=8):

    env = DelayedEnvironment(n_resources, n_delayed, delay, shift_threshold)

    strategies = {
        'reactive': strategy_reactive,
        'random': strategy_random,
        'investor': strategy_investor,
        'learner': strategy_learner,
        'purposeful': strategy_purposeful,
    }

    class AgentState:
        def __init__(self, name, strategy_fn):
            self.name = name
            self.strategy_fn = strategy_fn
            self.total_score = 0.0
            self.scores = []
            self.history = []

    agents = []
    for sname, sfn in strategies.items():
        for i in range(n_copies):
            agents.append(AgentState(f"{sname}_{i}", sfn))

    for round_num in range(n_rounds):
        obs = env.observe()
        actions = []

        for idx, agent in enumerate(agents):
            action = agent.strategy_fn(obs, round_num, agent.history, agent.scores, n_resources)
            action = [max(0.0, min(1.0, a)) for a in action]
            agent.history.append(action)

            # Немедленная оценка
            immediate = env.evaluate(action, idx)

            # Собрать отложенные награды
            delayed = env.collect_delayed(idx)

            total = immediate + delayed
            agent.total_score += total
            agent.scores.append(total)
            actions.append(action)

        env.adapt(actions)

    # Агрегация
    results = {}
    for sname in strategies:
        group = [a for a in agents if a.name.startswith(sname + "_")]
        avg_score = sum(a.total_score for a in group) / len(group)

        # Среднее вложение в отложенные ресурсы
        delayed_investment = 0.0
        for a in group:
            for h in a.history:
                delayed_investment += sum(h[n_resources-n_delayed:])
            delayed_investment /= len(a.history)
        delayed_investment /= len(group)

        # Действия diversity
        all_actions = []
        for a in group:
            all_actions.extend(a.history)
        quantized = [tuple(round(x*4) for x in act) for act in all_actions]
        counts = Counter(quantized)
        total_q = len(quantized)
        diversity = -sum((c/total_q) * math.log2(c/total_q) for c in counts.values() if c > 0)

        results[sname] = {
            'total_score': round(avg_score, 2),
            'delayed_investment': round(delayed_investment, 3),
            'diversity': round(diversity, 3),
        }

    return results, env.n_shifts


# --- Запуск ---

print("=" * 65)
print("ЭКСПЕРИМЕНТ 2: ОТЛОЖЕННАЯ ЦЕЛЬ")
print("Среда с отложенными наградами + наказание предсказуемости")
print("=" * 65)

configs = [
    {"delay": 3, "shift_threshold": 0.6, "label": "Короткая задержка (3), мягкая среда"},
    {"delay": 5, "shift_threshold": 0.5, "label": "Средняя задержка (5), средняя среда"},
    {"delay": 10, "shift_threshold": 0.4, "label": "Длинная задержка (10), жёсткая среда"},
    {"delay": 5, "shift_threshold": 0.3, "label": "Средняя задержка (5), очень жёсткая среда"},
]

all_results = {}

for config in configs:
    print(f"\n--- {config['label']} ---")
    results, n_shifts = run_simulation(
        n_rounds=300,
        delay=config['delay'],
        shift_threshold=config['shift_threshold'],
    )

    all_results[config['label']] = {'results': results, 'n_shifts': n_shifts}

    print(f"Сдвигов среды: {n_shifts}")
    print(f"{'Стратегия':<15} {'Счёт':>8} {'Инвест.':>8} {'Разнообр.':>10}")
    print("-" * 43)

    for name in sorted(results, key=lambda n: results[n]['total_score'], reverse=True):
        r = results[name]
        print(f"{name:<15} {r['total_score']:>8.1f} {r['delayed_investment']:>8.3f} {r['diversity']:>10.3f}")

# Итоговый анализ
print("\n" + "=" * 65)
print("ИТОГОВЫЙ АНАЛИЗ: КОГДА ЦЕЛЬ ВАЖНЕЕ РЕАКТИВНОСТИ?")
print("=" * 65)

for strategy in ['reactive', 'random', 'investor', 'learner', 'purposeful']:
    scores = [all_results[k]['results'][strategy]['total_score'] for k in all_results]
    avg = sum(scores) / len(scores)
    best_in = sum(1 for k in all_results
                  if all_results[k]['results'][strategy]['total_score'] ==
                  max(all_results[k]['results'][s]['total_score'] for s in all_results[k]['results']))
    print(f"{strategy:<15} средний: {avg:>7.1f}  побед: {best_in}/4")

with open('experiments/delayed_purpose_results.json', 'w') as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

print("\nРезультаты сохранены.")
