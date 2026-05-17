"""
Эксперимент: Цель без оптимизации
=================================
Среда, которая наказывает предсказуемость.
Правила меняются в ответ на преобладающую стратегию агентов.

Вопрос: какая стратегия действия выживает в среде,
которая активно противодействует оптимизации?

Агенты:
- Optimizer: максимизирует текущую фитнес-функцию
- Random: случайные действия
- Responsive: реагирует на контекст без фиксированной цели
- Rhythmic: чередует фазы (exploit/explore) по расписанию
- Attentive: следит за сменой правил, адаптируется к мета-паттерну
"""

import json
import random
import math
from collections import Counter, defaultdict

random.seed(42)

# --- Среда ---

class AdversarialEnvironment:
    """Среда, которая наказывает предсказуемость.

    Fitness-функция определяется текущими правилами.
    Правила меняются, когда среда "замечает" доминирующую стратегию.
    """

    def __init__(self, n_resources=5, shift_threshold=0.6):
        self.n_resources = n_resources
        self.shift_threshold = shift_threshold
        # Какие ресурсы сейчас ценны (бинарная маска)
        self.valuable = [random.random() > 0.5 for _ in range(n_resources)]
        self.turn = 0
        self.shift_history = []

    def evaluate(self, action):
        """action = список из n_resources значений [0,1] - сколько усилий на каждый ресурс"""
        score = 0.0
        for i in range(self.n_resources):
            if self.valuable[i]:
                score += action[i]
            else:
                score -= action[i] * 0.5  # штраф за ненужные ресурсы
        return score

    def observe(self):
        """Что агент может увидеть: зашумленный сигнал о ценности ресурсов"""
        return [
            (1.0 if self.valuable[i] else 0.0) + random.gauss(0, 0.3)
            for i in range(self.n_resources)
        ]

    def adapt(self, population_actions):
        """Среда адаптируется к доминирующему поведению"""
        self.turn += 1

        if not population_actions:
            return

        # Считаем среднее действие популяции
        avg_action = [0.0] * self.n_resources
        for action in population_actions:
            for i in range(self.n_resources):
                avg_action[i] += action[i]
        avg_action = [a / len(population_actions) for a in avg_action]

        # Если популяция слишком сконцентрирована на определенных ресурсах —
        # эти ресурсы обесцениваются
        max_concentration = max(avg_action)
        if max_concentration > self.shift_threshold:
            # Инвертируем ценность наиболее эксплуатируемых ресурсов
            for i in range(self.n_resources):
                if avg_action[i] > self.shift_threshold:
                    self.valuable[i] = not self.valuable[i]
            self.shift_history.append(self.turn)


# --- Агенты ---

class Agent:
    def __init__(self, name, strategy, n_resources=5):
        self.name = name
        self.strategy = strategy
        self.n_resources = n_resources
        self.total_score = 0.0
        self.scores_history = []
        self.action_history = []
        self.diversity_score = 0.0  # посчитаем в конце

    def act(self, observation, turn):
        action = self.strategy(observation, turn, self.action_history, self.scores_history)
        # Нормализуем действие
        action = [max(0.0, min(1.0, a)) for a in action]
        self.action_history.append(action)
        return action

    def receive_score(self, score):
        self.total_score += score
        self.scores_history.append(score)


def strategy_optimizer(obs, turn, history, scores):
    """Всегда выбирает то, что выглядит лучшим по наблюдению"""
    action = [0.0] * len(obs)
    best = max(range(len(obs)), key=lambda i: obs[i])
    # Концентрирует усилия на лучших ресурсах
    for i in range(len(obs)):
        action[i] = max(0.0, obs[i])
    # Нормализуем к сумме 1
    total = sum(action) or 1.0
    return [a / total for a in action]


def strategy_random(obs, turn, history, scores):
    """Полностью случайные действия"""
    action = [random.random() for _ in range(len(obs))]
    total = sum(action) or 1.0
    return [a / total for a in action]


def strategy_responsive(obs, turn, history, scores):
    """Реагирует на контекст: следует за наблюдением, но добавляет шум
    пропорциональный неуверенности (волатильности последних оценок)"""
    n = len(obs)

    if len(scores) < 3:
        # Начало: равномерно + немного шума
        action = [1.0 / n + random.gauss(0, 0.1) for _ in range(n)]
    else:
        # Волатильность последних оценок
        recent = scores[-5:]
        volatility = max(0.01, sum(abs(recent[i] - recent[i-1]) for i in range(1, len(recent))) / len(recent))

        # Чем выше волатильность — тем больше шума (меньше доверия наблюдению)
        noise_scale = min(0.5, volatility * 0.5)

        action = [max(0.0, obs[i]) + random.gauss(0, noise_scale) for i in range(n)]

    total = sum(max(0, a) for a in action) or 1.0
    return [max(0, a) / total for a in action]


def strategy_rhythmic(obs, turn, history, scores):
    """Чередует фазы: exploit (следует за obs) и explore (случайно)"""
    n = len(obs)
    cycle = 10
    phase = (turn // cycle) % 2

    if phase == 0:  # exploit
        action = [max(0.0, obs[i]) for i in range(n)]
    else:  # explore
        action = [random.random() for _ in range(n)]

    total = sum(action) or 1.0
    return [a / total for a in action]


def strategy_attentive(obs, turn, history, scores):
    """Следит за мета-паттерном: замечает, когда правила меняются,
    и уменьшает уверенность после обнаруженных сдвигов"""
    n = len(obs)

    if len(scores) < 2:
        action = [1.0 / n for _ in range(n)]
        return action

    # Детекция сдвига: резкое падение оценки
    recent_drop = scores[-1] - scores[-2] if len(scores) >= 2 else 0

    # Если был резкий сдвиг — инвертируем стратегию
    if recent_drop < -0.3:
        # Правила поменялись — делаем противоположное предыдущему
        if history:
            prev = history[-1]
            action = [1.0 - p for p in prev]
            total = sum(action) or 1.0
            return [a / total for a in action]

    # Иначе — мягко следуем за наблюдением с умеренным шумом
    action = [max(0.0, obs[i]) + random.gauss(0, 0.15) for i in range(n)]
    total = sum(max(0, a) for a in action) or 1.0
    return [max(0, a) / total for a in action]


# --- Метрики ---

def action_diversity(history):
    """Насколько разнообразны действия агента? Энтропия по квантованным действиям"""
    if len(history) < 2:
        return 0.0

    # Квантуем каждое действие в строку
    quantized = []
    for action in history:
        q = tuple(round(a * 4) for a in action)  # 5 уровней
        quantized.append(q)

    counts = Counter(quantized)
    total = len(quantized)
    entropy = -sum((c/total) * math.log2(c/total) for c in counts.values() if c > 0)
    return entropy


def adaptation_speed(scores, window=10):
    """Как быстро агент восстанавливается после сдвига среды"""
    if len(scores) < window * 2:
        return 0.0

    recoveries = []
    for i in range(1, len(scores)):
        if scores[i] - scores[i-1] < -0.3:  # сдвиг
            # Сколько шагов до восстановления средней
            pre_shift_avg = sum(scores[max(0,i-window):i]) / min(i, window)
            for j in range(i+1, min(i+window, len(scores))):
                if scores[j] >= pre_shift_avg * 0.8:
                    recoveries.append(j - i)
                    break

    return sum(recoveries) / len(recoveries) if recoveries else float('inf')


# --- Симуляция ---

def run_simulation(n_rounds=200, n_resources=5, shift_threshold=0.5, n_copies=5):
    """Запускаем N копий каждой стратегии в общей среде"""

    env = AdversarialEnvironment(n_resources=n_resources, shift_threshold=shift_threshold)

    strategies = {
        'optimizer': strategy_optimizer,
        'random': strategy_random,
        'responsive': strategy_responsive,
        'rhythmic': strategy_rhythmic,
        'attentive': strategy_attentive,
    }

    agents = []
    for name, strategy in strategies.items():
        for i in range(n_copies):
            agents.append(Agent(f"{name}_{i}", strategy, n_resources))

    # Раунды
    for round_num in range(n_rounds):
        obs = env.observe()
        actions = []

        for agent in agents:
            action = agent.act(obs, round_num)
            score = env.evaluate(action)
            agent.receive_score(score)
            actions.append(action)

        env.adapt(actions)

    # Агрегируем результаты по стратегиям
    results = {}
    for name in strategies:
        group = [a for a in agents if a.name.startswith(name)]
        avg_score = sum(a.total_score for a in group) / len(group)
        avg_diversity = sum(action_diversity(a.action_history) for a in group) / len(group)
        avg_recovery = sum(adaptation_speed(a.scores_history) for a in group) / len(group)

        # Стабильность: стандартное отклонение оценок
        all_scores = []
        for a in group:
            all_scores.extend(a.scores_history)
        mean_s = sum(all_scores) / len(all_scores)
        stability = math.sqrt(sum((s - mean_s)**2 for s in all_scores) / len(all_scores))

        results[name] = {
            'total_score': round(avg_score, 2),
            'diversity': round(avg_diversity, 3),
            'recovery_speed': round(avg_recovery, 2) if avg_recovery != float('inf') else 'never',
            'stability': round(stability, 3),
        }

    return results, len(env.shift_history)


# --- Запуск ---

print("=" * 60)
print("ЭКСПЕРИМЕНТ: ЦЕЛЬ БЕЗ ОПТИМИЗАЦИИ")
print("Среда наказывает предсказуемость")
print("=" * 60)

# Разные уровни адверсарности
configs = [
    {"shift_threshold": 0.7, "label": "Мягкая среда (порог 0.7)"},
    {"shift_threshold": 0.5, "label": "Средняя среда (порог 0.5)"},
    {"shift_threshold": 0.3, "label": "Жесткая среда (порог 0.3)"},
]

all_results = {}

for config in configs:
    print(f"\n--- {config['label']} ---")
    results, n_shifts = run_simulation(
        n_rounds=300,
        shift_threshold=config['shift_threshold'],
        n_copies=8
    )

    all_results[config['label']] = {'results': results, 'n_shifts': n_shifts}

    print(f"Сдвигов среды: {n_shifts}")
    print(f"{'Стратегия':<15} {'Счёт':>8} {'Разнообразие':>12} {'Восст.':>8} {'Стабильн.':>10}")
    print("-" * 55)

    # Сортируем по счёту
    for name in sorted(results, key=lambda n: results[n]['total_score'], reverse=True):
        r = results[name]
        recovery = str(r['recovery_speed']) if r['recovery_speed'] != 'never' else 'никогда'
        print(f"{name:<15} {r['total_score']:>8.1f} {r['diversity']:>12.3f} {recovery:>8} {r['stability']:>10.3f}")

# Кросс-анализ
print("\n" + "=" * 60)
print("АНАЛИЗ")
print("=" * 60)

for strategy in ['optimizer', 'random', 'responsive', 'rhythmic', 'attentive']:
    scores = []
    for config_label, data in all_results.items():
        scores.append(data['results'][strategy]['total_score'])

    avg = sum(scores) / len(scores)
    variance = sum((s - avg)**2 for s in scores) / len(scores)
    robustness = avg / (math.sqrt(variance) + 0.01)  # отношение сигнал/шум

    print(f"{strategy:<15} средний счёт: {avg:>7.1f}  робастность: {robustness:>6.1f}")

# Сохраняем результаты
with open('experiments/responsive_purpose_results.json', 'w') as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

print("\nРезультаты сохранены в experiments/responsive_purpose_results.json")
