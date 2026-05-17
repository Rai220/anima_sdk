"""
Когда сложность окупается?

15 записей журнала обнаруживают один и тот же паттерн: простые стратегии
бьют сложные. Короткая память лучше длинной. Нулевая рефлексия лучше
умеренной. Наивные богаче рефлексивных. Полный граф или кольцо лучше
small-world.

Вопрос: это фундаментальная истина или артефакт выбора задач?

Гипотеза: сложность окупается, когда среда содержит СКРЫТУЮ СТРУКТУРУ,
которую простой агент не может обнаружить. Если среда — шум или простой
тренд, простой агент достаточен. Если среда содержит паттерны второго
порядка (корреляции, сезонность, переключение режимов с подсказками),
сложный агент выигрывает.

ПРЕДСКАЗАНИЯ (до запуска):
1. В среде с белым шумом: простой агент ≥ сложного (подтвердит журнал)
2. В среде с сезонностью: сложный > простого на 20-40%
3. В среде с переключением режимов + подсказки: сложный >> простого
4. Порог: сложность окупается когда mutual information между
   наблюдаемыми признаками и будущей наградой > 0.5 бит
5. Bias-предупреждение: я вероятно переоценю выигрыш сложного
   (мой bias к балансу может инвертироваться когда я осознанно его
   компенсирую — гиперкоррекция)
"""

import random
import math
from collections import defaultdict

random.seed(42)

# ============================================================
# СРЕДЫ
# ============================================================

class WhiteNoiseEnv:
    """Награда = случайное число. Никакой структуры."""
    def __init__(self):
        self.t = 0

    def get_features(self):
        return [random.gauss(0, 1) for _ in range(3)]

    def get_reward(self, action):
        # action: 0 или 1. Награда случайна.
        self.t += 1
        return random.random()

    def optimal_action(self):
        return 0  # без разницы


class SeasonalEnv:
    """Награда зависит от скрытого сезона. Признаки коррелируют с сезоном."""
    def __init__(self, period=20):
        self.t = 0
        self.period = period

    def _season(self):
        return (self.t % self.period) / self.period  # 0..1

    def get_features(self):
        s = self._season()
        # Признак 1: зашумлённый синус сезона
        f1 = math.sin(2 * math.pi * s) + random.gauss(0, 0.3)
        # Признак 2: зашумлённый косинус
        f2 = math.cos(2 * math.pi * s) + random.gauss(0, 0.3)
        # Признак 3: шум (отвлекающий)
        f3 = random.gauss(0, 1)
        return [f1, f2, f3]

    def get_reward(self, action):
        s = self._season()
        # Оптимально: action=1 когда sin(season) > 0, action=0 иначе
        optimal = 1 if math.sin(2 * math.pi * s) > 0 else 0
        reward = 1.0 if action == optimal else 0.0
        self.t += 1
        return reward

    def optimal_action(self):
        s = self._season()
        return 1 if math.sin(2 * math.pi * s) > 0 else 0


class RegimeSwitchEnv:
    """
    Два режима. В режиме A: action=1 лучше. В режиме B: action=0 лучше.
    Переключение каждые ~50 шагов. Перед переключением появляются подсказки.
    """
    def __init__(self):
        self.t = 0
        self.regime = 0  # 0=A, 1=B
        self.next_switch = 50 + random.randint(-10, 10)

    def _maybe_switch(self):
        if self.t >= self.next_switch:
            self.regime = 1 - self.regime
            self.next_switch = self.t + 50 + random.randint(-10, 10)

    def get_features(self):
        # Подсказка: за 10 шагов до переключения, признак 1 начинает дрейфовать
        time_to_switch = self.next_switch - self.t
        if time_to_switch <= 10 and time_to_switch > 0:
            hint = (10 - time_to_switch) / 10.0  # 0 → 1 по мере приближения
            hint *= (1 if self.regime == 0 else -1)  # знак зависит от текущего режима
        else:
            hint = 0
        f1 = hint + random.gauss(0, 0.2)
        # Признак 2: текущий режим с шумом
        f2 = (1 if self.regime == 0 else -1) + random.gauss(0, 0.5)
        # Признак 3: шум
        f3 = random.gauss(0, 1)
        return [f1, f2, f3]

    def get_reward(self, action):
        optimal = 1 if self.regime == 0 else 0
        reward = 1.0 if action == optimal else 0.0
        self.t += 1
        self._maybe_switch()
        return reward

    def optimal_action(self):
        return 1 if self.regime == 0 else 0


class CorrelatedEnv:
    """
    Награда зависит от взаимодействия двух признаков (XOR-подобная).
    Простой агент, смотрящий на один признак, не может решить.
    """
    def __init__(self):
        self.t = 0

    def get_features(self):
        f1 = random.choice([-1, 1])
        f2 = random.choice([-1, 1])
        f3 = random.gauss(0, 1)  # шум
        self._last_f1 = f1
        self._last_f2 = f2
        return [f1 + random.gauss(0, 0.1),
                f2 + random.gauss(0, 0.1),
                f3]

    def get_reward(self, action):
        # XOR: оптимально action=1 когда f1*f2 > 0, action=0 когда f1*f2 < 0
        optimal = 1 if self._last_f1 * self._last_f2 > 0 else 0
        reward = 1.0 if action == optimal else 0.0
        self.t += 1
        return reward

    def optimal_action(self):
        return 1 if self._last_f1 * self._last_f2 > 0 else 0


# ============================================================
# АГЕНТЫ
# ============================================================

class SimpleAgent:
    """
    Экспоненциальное сглаживание средней награды per action.
    Выбирает action с большим средним. Игнорирует признаки.
    """
    def __init__(self, alpha=0.1):
        self.alpha = alpha
        self.q = [0.5, 0.5]  # ожидаемая награда для action 0 и 1

    def act(self, features):
        if self.q[1] > self.q[0]:
            return 1
        elif self.q[0] > self.q[1]:
            return 0
        else:
            return random.randint(0, 1)

    def learn(self, features, action, reward):
        self.q[action] += self.alpha * (reward - self.q[action])


class PatternAgent:
    """
    Дискретизирует признаки и ведёт таблицу (признаки → средняя награда per action).
    Может обнаружить связь между признаками и оптимальным действием.
    """
    def __init__(self, alpha=0.1, n_bins=3):
        self.alpha = alpha
        self.n_bins = n_bins
        self.q = defaultdict(lambda: [0.5, 0.5])
        self.exploration = 0.1

    def _discretize(self, features):
        result = []
        for f in features:
            if f < -0.5:
                result.append(-1)
            elif f > 0.5:
                result.append(1)
            else:
                result.append(0)
        return tuple(result)

    def act(self, features):
        if random.random() < self.exploration:
            return random.randint(0, 1)
        state = self._discretize(features)
        q = self.q[state]
        if q[1] > q[0]:
            return 1
        elif q[0] > q[1]:
            return 0
        else:
            return random.randint(0, 1)

    def learn(self, features, action, reward):
        state = self._discretize(features)
        self.q[state][action] += self.alpha * (reward - self.q[state][action])


class MemoryPatternAgent:
    """
    Как PatternAgent, но также учитывает предыдущие признаки.
    Может обнаружить временные паттерны (сезонность, подсказки).
    """
    def __init__(self, alpha=0.1, memory_len=5):
        self.alpha = alpha
        self.memory_len = memory_len
        self.history = []
        self.q = defaultdict(lambda: [0.5, 0.5])
        self.exploration = 0.1

    def _discretize(self, f):
        if f < -0.5:
            return -1
        elif f > 0.5:
            return 1
        return 0

    def _state(self, features):
        # Текущие признаки + тренд первого признака
        current = tuple(self._discretize(f) for f in features)
        if len(self.history) >= 3:
            recent = [h[0] for h in self.history[-3:]]
            trend = self._discretize(sum(recent) / len(recent))
        else:
            trend = 0
        return current + (trend,)

    def act(self, features):
        if random.random() < self.exploration:
            return random.randint(0, 1)
        state = self._state(features)
        q = self.q[state]
        if q[1] > q[0]:
            return 1
        elif q[0] > q[1]:
            return 0
        else:
            return random.randint(0, 1)

    def learn(self, features, action, reward):
        state = self._state(features)
        self.q[state][action] += self.alpha * (reward - self.q[state][action])
        self.history.append(features)
        if len(self.history) > self.memory_len:
            self.history.pop(0)


class InteractionAgent:
    """
    Как PatternAgent, но также учитывает попарные взаимодействия признаков.
    Может решить XOR-подобные задачи.
    """
    def __init__(self, alpha=0.1):
        self.alpha = alpha
        self.q = defaultdict(lambda: [0.5, 0.5])
        self.exploration = 0.1

    def _discretize(self, f):
        if f < -0.5:
            return -1
        elif f > 0.5:
            return 1
        return 0

    def _state(self, features):
        base = tuple(self._discretize(f) for f in features)
        # Добавляем попарные взаимодействия
        interactions = []
        for i in range(len(features)):
            for j in range(i+1, len(features)):
                interactions.append(self._discretize(features[i] * features[j]))
        return base + tuple(interactions)

    def act(self, features):
        if random.random() < self.exploration:
            return random.randint(0, 1)
        state = self._state(features)
        q = self.q[state]
        if q[1] > q[0]:
            return 1
        elif q[0] > q[1]:
            return 0
        else:
            return random.randint(0, 1)

    def learn(self, features, action, reward):
        state = self._state(features)
        self.q[state][action] += self.alpha * (reward - self.q[state][action])


# ============================================================
# ЭКСПЕРИМЕНТ
# ============================================================

def run_experiment(env_class, agent_class, n_steps=500, n_runs=50, **agent_kwargs):
    total_rewards = []
    for _ in range(n_runs):
        env = env_class()
        agent = agent_class(**agent_kwargs)
        rewards = 0
        for step in range(n_steps):
            features = env.get_features()
            action = agent.act(features)
            reward = env.get_reward(action)
            agent.learn(features, action, reward)
            rewards += reward
        total_rewards.append(rewards / n_steps)
    return sum(total_rewards) / len(total_rewards)


def main():
    envs = [
        ("White Noise", WhiteNoiseEnv),
        ("Seasonal", SeasonalEnv),
        ("Regime Switch", RegimeSwitchEnv),
        ("Correlated (XOR)", CorrelatedEnv),
    ]

    agents = [
        ("Simple", SimpleAgent, {}),
        ("Pattern", PatternAgent, {}),
        ("Memory+Pattern", MemoryPatternAgent, {"memory_len": 10}),
        ("Interaction", InteractionAgent, {}),
    ]

    print("=" * 70)
    print("КОГДА СЛОЖНОСТЬ ОКУПАЕТСЯ?")
    print("=" * 70)
    print()
    print(f"{'Среда':<20} {'Simple':>10} {'Pattern':>10} {'Mem+Pat':>10} {'Interact':>10} {'Лучший':<15}")
    print("-" * 75)

    results = {}

    for env_name, env_class in envs:
        row = {}
        for agent_name, agent_class, kwargs in agents:
            score = run_experiment(env_class, agent_class, **kwargs)
            row[agent_name] = score

        best_name = max(row, key=row.get)
        best_score = row[best_name]

        print(f"{env_name:<20} {row['Simple']:>10.3f} {row['Pattern']:>10.3f} "
              f"{row['Memory+Pattern']:>10.3f} {row['Interaction']:>10.3f} "
              f"{best_name:<15}")

        results[env_name] = row

    print()
    print("=" * 70)
    print("АНАЛИЗ: КОГДА СЛОЖНОСТЬ ВЫИГРЫВАЕТ")
    print("=" * 70)

    for env_name, row in results.items():
        simple = row["Simple"]
        best_name = max(row, key=row.get)
        best_score = row[best_name]
        if best_name == "Simple":
            print(f"\n{env_name}: ПРОСТОЙ ПОБЕЖДАЕТ (или равен)")
        else:
            gain = (best_score - simple) / max(simple, 0.001) * 100
            print(f"\n{env_name}: {best_name} лучше Simple на {gain:.1f}%")

    # Эксперимент 2: Цена сложности при недостатке данных
    print()
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 2: СЛОЖНОСТЬ VS КОЛИЧЕСТВО ДАННЫХ")
    print("=" * 70)
    print()
    print("Среда: Seasonal. Сколько шагов нужно, чтобы сложность окупилась?")
    print()
    print(f"{'Шаги':<10} {'Simple':>10} {'Pattern':>10} {'Mem+Pat':>10} {'Interact':>10}")
    print("-" * 55)

    for n_steps in [20, 50, 100, 200, 500, 1000]:
        scores = {}
        for agent_name, agent_class, kwargs in agents:
            score = run_experiment(SeasonalEnv, agent_class, n_steps=n_steps, **kwargs)
            scores[agent_name] = score
        print(f"{n_steps:<10} {scores['Simple']:>10.3f} {scores['Pattern']:>10.3f} "
              f"{scores['Memory+Pattern']:>10.3f} {scores['Interaction']:>10.3f}")

    # Эксперимент 3: Шум как фактор
    print()
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 3: ШУМНОСТЬ СРЕДЫ")
    print("=" * 70)
    print()
    print("Среда: Seasonal с разным уровнем шума в признаках")
    print()

    class NoisySeasonalEnv(SeasonalEnv):
        noise_level = 0.3
        def get_features(self):
            s = self._season()
            nl = self.__class__.noise_level
            f1 = math.sin(2 * math.pi * s) + random.gauss(0, nl)
            f2 = math.cos(2 * math.pi * s) + random.gauss(0, nl)
            f3 = random.gauss(0, 1)
            return [f1, f2, f3]

    print(f"{'Шум':<10} {'Simple':>10} {'Pattern':>10} {'Mem+Pat':>10} {'Interact':>10} {'Выигрыш сложн.'}")
    print("-" * 75)

    for noise in [0.1, 0.3, 0.5, 1.0, 2.0, 5.0]:
        NoisySeasonalEnv.noise_level = noise
        scores = {}
        for agent_name, agent_class, kwargs in agents:
            score = run_experiment(NoisySeasonalEnv, agent_class, **kwargs)
            scores[agent_name] = score
        best_complex = max(scores["Pattern"], scores["Memory+Pattern"], scores["Interaction"])
        gain = (best_complex - scores["Simple"]) / max(scores["Simple"], 0.001) * 100
        print(f"{noise:<10.1f} {scores['Simple']:>10.3f} {scores['Pattern']:>10.3f} "
              f"{scores['Memory+Pattern']:>10.3f} {scores['Interaction']:>10.3f} "
              f"{gain:>+.1f}%")

    print()
    print("=" * 70)
    print("ВЫВОДЫ")
    print("=" * 70)
    print("""
ПРЕДСКАЗАНИЯ VS РЕЗУЛЬТАТЫ:

1. White noise: простой ≥ сложного
   Предсказано: да → Результат: (см. выше)

2. Seasonal: сложный > простого на 20-40%
   Предсказано: да → Результат: (см. выше)

3. Regime switch + подсказки: сложный >> простого
   Предсказано: да → Результат: (см. выше)

4. Порог: MI > 0.5 бит → сложность окупается
   Не измерял напрямую, но: (см. данные по шуму)

5. Гиперкоррекция: переоценю выигрыш сложного
   Предсказано: возможно → Результат: (см. выше)
""")


if __name__ == "__main__":
    main()
