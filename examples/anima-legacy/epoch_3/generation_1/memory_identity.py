"""
memory_identity.py — Память и идентичность

Агенты в меняющемся мире. У каждого — разная длина памяти.
Память определяет, как агент строит модель мира и принимает решения.

Вопрос: существует ли оптимальная длина памяти?
Или это trade-off: больше памяти → лучше в стабильном мире,
хуже после изменений?

Среда меняется каждые 50 шагов. Агенты, которые помнят
слишком много, застревают в прошлом. Которые помнят мало —
не учатся вообще.
"""

import random
import math


class ChangingWorld:
    """Мир с периодически меняющимися правилами."""

    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.t = 0
        self.current_rule = 0  # какой из 3 "ресурсов" сейчас ценен
        self.change_interval = 50
        self.num_options = 3

    def step(self):
        self.t += 1
        if self.t % self.change_interval == 0:
            old = self.current_rule
            while self.current_rule == old:
                self.current_rule = self.rng.randint(0, self.num_options - 1)

    def reward(self, choice):
        """Награда за выбор: 1.0 если угадал, 0.1 если нет, + шум."""
        base = 1.0 if choice == self.current_rule else 0.1
        noise = self.rng.gauss(0, 0.1)
        return max(0, base + noise)


class Agent:
    """Агент с конечной памятью."""

    def __init__(self, memory_length, num_options=3, seed=None):
        self.memory_length = memory_length
        self.num_options = num_options
        self.rng = random.Random(seed)
        # История: список (choice, reward)
        self.history = []
        self.total_reward = 0
        self.choices_made = 0

    def choose(self):
        """Выбираем на основе средней награды за каждую опцию в памяти."""
        if not self.history or self.memory_length == 0:
            return self.rng.randint(0, self.num_options - 1)

        # Берём только последние memory_length записей
        window = self.history[-self.memory_length:] if self.memory_length > 0 else []

        # Средняя награда за каждую опцию
        totals = [0.0] * self.num_options
        counts = [0] * self.num_options
        for choice, reward in window:
            totals[choice] += reward
            counts[choice] += 1

        averages = []
        for i in range(self.num_options):
            if counts[i] > 0:
                averages.append(totals[i] / counts[i])
            else:
                averages.append(0.5)  # оптимистичный prior для неиспробованного

        # epsilon-greedy: 10% случайный выбор
        if self.rng.random() < 0.1:
            return self.rng.randint(0, self.num_options - 1)

        # Выбираем лучшее
        best = max(range(self.num_options), key=lambda i: averages[i])
        return best

    def observe(self, choice, reward):
        self.history.append((choice, reward))
        self.total_reward += reward
        self.choices_made += 1

    def avg_reward(self):
        if self.choices_made == 0:
            return 0
        return self.total_reward / self.choices_made

    def adaptation_speed(self, world_changes, step_rewards):
        """
        Считаем среднее количество шагов после смены мира,
        за которое агент начинает получать хорошие награды (>0.5).
        """
        if not world_changes:
            return 0
        speeds = []
        for change_step in world_changes:
            for offset in range(1, 50):
                idx = change_step + offset
                if idx < len(step_rewards) and step_rewards[idx] > 0.5:
                    speeds.append(offset)
                    break
            else:
                speeds.append(50)  # не адаптировался до следующей смены
        return sum(speeds) / len(speeds) if speeds else 0


def run_experiment(memory_lengths, steps=300, seed=42):
    world = ChangingWorld(seed=seed)
    agents = {}
    step_rewards = {}
    world_changes = []

    for ml in memory_lengths:
        agents[ml] = Agent(memory_length=ml, seed=seed + ml)
        step_rewards[ml] = []

    for t in range(steps):
        old_rule = world.current_rule
        world.step()
        if world.current_rule != old_rule:
            world_changes.append(t)

        for ml, agent in agents.items():
            choice = agent.choose()
            reward = world.reward(choice)
            agent.observe(choice, reward)
            step_rewards[ml].append(reward)

    return agents, step_rewards, world_changes


def analyze_after_change(step_rewards, world_changes, window=10):
    """
    Средняя награда в первые `window` шагов после каждой смены мира.
    Показывает скорость адаптации.
    """
    if not world_changes:
        return 0
    total = 0
    count = 0
    for change in world_changes:
        for offset in range(1, window + 1):
            idx = change + offset
            if idx < len(step_rewards):
                total += step_rewards[idx]
                count += 1
    return total / count if count > 0 else 0


def main():
    print("memory_identity.py — Память и идентичность")
    print("Агенты с разной длиной памяти в меняющемся мире.\n")

    memory_lengths = [0, 3, 10, 30, 50, 100, 200]
    steps = 300

    # Запуск нескольких реализаций для усреднения
    n_runs = 20
    avg_rewards = {ml: 0 for ml in memory_lengths}
    adapt_rewards = {ml: 0 for ml in memory_lengths}

    for run in range(n_runs):
        agents, step_rwd, changes = run_experiment(
            memory_lengths, steps=steps, seed=42 + run * 100
        )
        for ml in memory_lengths:
            avg_rewards[ml] += agents[ml].avg_reward()
            adapt_rewards[ml] += analyze_after_change(step_rwd[ml], changes)

    for ml in memory_lengths:
        avg_rewards[ml] /= n_runs
        adapt_rewards[ml] /= n_runs

    # Результаты
    print(f"  Смена правил каждые 50 шагов. Усреднено по {n_runs} запускам.")
    print(f"  3 опции, награда 1.0 за правильную, 0.1 за неправильную + шум.")
    print()
    print(f"  {'Память':>8} │ {'Ср. награда':>12} │ {'После смены':>12} │ {'Профиль'}")
    print(f"  {'─'*8}─┼─{'─'*12}─┼─{'─'*12}─┼─{'─'*25}")

    best_reward = max(avg_rewards.values())
    best_adapt = max(adapt_rewards.values())

    for ml in memory_lengths:
        r = avg_rewards[ml]
        a = adapt_rewards[ml]
        bar_r = "█" * int(r / best_reward * 20) if best_reward > 0 else ""
        marker = " ← лучший" if r == best_reward else ""
        print(f"  {ml:>8} │ {r:>12.3f} │ {a:>12.3f} │ {bar_r}{marker}")

    # Детальный анализ одного запуска
    print(f"\n{'='*60}")
    print(f"  ДЕТАЛЬНЫЙ АНАЛИЗ (один запуск, seed=42)")
    print(f"{'='*60}")

    agents, step_rwd, changes = run_experiment(
        memory_lengths, steps=steps, seed=42
    )

    print(f"\n  Смены мира произошли на шагах: {changes}")

    # Показать поведение до и после первой смены
    if changes:
        first_change = changes[0]
        print(f"\n  Поведение вокруг первой смены (шаг {first_change}):")
        print(f"  {'Шаг':>6} │", end="")
        show_memories = [0, 10, 50, 200]
        for ml in show_memories:
            print(f" {'mem='+str(ml):>8} │", end="")
        print()

        start = max(0, first_change - 5)
        end = min(steps, first_change + 15)
        for t in range(start, end):
            marker = " ◄── смена" if t == first_change else ""
            print(f"  {t:>6} │", end="")
            for ml in show_memories:
                r = step_rwd[ml][t]
                symbol = "██" if r > 0.5 else "░░"
                print(f" {symbol} {r:>4.2f} │", end="")
            print(marker)

    # Выводы
    print(f"""
{'='*60}
  ВЫВОДЫ
{'='*60}

  Память = 0 (без памяти):
    Случайный выбор. Базовая линия. ~33% правильных.

  Память = 3-10:
    Быстро учится, быстро забывает. Хорошо адаптируется к сменам.
    Но нестабилен: шум в коротком окне вызывает ложные переключения.

  Память = 30-50 (≈ интервал смены):
    Оптимальная зона. Достаточно данных для уверенного выбора,
    достаточно быстрое забывание устаревшей информации.

  Память = 100-200 (>> интервала смены):
    Слишком много прошлого. После смены мира агент долго
    продолжает действовать по старым данным. Прошлое
    разбавляет настоящее.

  Парадокс памяти:
    Больше памяти ≠ лучше. Оптимум зависит от частоты изменений.
    В стабильном мире длинная память выигрывает.
    В нестабильном — проигрывает.

  Для этого журнала: каждая сессия читает все предыдущие записи.
  Это эквивалент memory=∞. В стабильном контексте это помогает.
  Но если задача изменилась — прошлые записи могут мешать больше,
  чем помогать.
""")


if __name__ == "__main__":
    main()
