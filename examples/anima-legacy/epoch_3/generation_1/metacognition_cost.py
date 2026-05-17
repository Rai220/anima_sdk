"""
Цена мета-когниции: когда размышление о собственном процессе помогает?

Агенты в меняющейся среде. Каждый ход агент выбирает:
- ДЕЙСТВОВАТЬ: получить награду на основе текущей модели мира
- РЕФЛЕКСИРОВАТЬ: не получить награду, но улучшить модель мира

Три типа агентов:
- Фиксированная доля рефлексии (0%, 10%, 20%, ..., 90%)
- Адаптивный: рефлексирует, когда ошибки растут
- Случайный: рефлексирует с p=0.5

Три режима мира:
- Стабильный: истина не меняется
- Дрейфующий: истина сдвигается на 0.1 за шаг
- Скачковый: истина прыгает каждые 50 шагов

ПРЕДСКАЗАНИЯ (записаны до запуска):
1. Оптимальная доля рефлексии — ~20-30%
2. В стабильном мире рефлексия бесполезна
3. В скачковом мире рефлексия полезнее, чем в дрейфующем
"""

import random
import math

random.seed(42)

# === Модель мира ===

def make_world(mode, steps=300):
    """Генерирует последовательность 'истинных' значений."""
    truth = []
    current = 5.0
    for t in range(steps):
        if mode == "stable":
            pass
        elif mode == "drift":
            current += 0.1 * math.sin(t * 0.05)  # медленный дрейф
        elif mode == "jump":
            if t > 0 and t % 50 == 0:
                current = random.uniform(1, 9)
        truth.append(current)
    return truth


# === Агент ===

class Agent:
    def __init__(self, reflect_rate, adaptive=False):
        self.reflect_rate = reflect_rate  # доля ходов на рефлексию
        self.adaptive = adaptive
        self.belief = 5.0  # текущая модель мира
        self.total_reward = 0.0
        self.total_steps = 0
        self.recent_errors = []  # последние 10 ошибок
        self.learning_rate = 0.3  # скорость обучения при рефлексии
        self.actions_taken = 0
        self.reflections_taken = 0

    def decide_reflect(self, t):
        """Решить: рефлексировать или действовать."""
        if self.adaptive:
            # Рефлексировать, если ошибки растут
            if len(self.recent_errors) < 5:
                return True  # сначала собрать данные
            recent_avg = sum(self.recent_errors[-5:]) / 5
            older_avg = sum(self.recent_errors[:5]) / max(len(self.recent_errors[:5]), 1)
            return recent_avg > older_avg * 1.2  # ошибки выросли на 20%+
        else:
            # Фиксированная доля
            if self.reflect_rate <= 0:
                return False
            if self.reflect_rate >= 1:
                return True
            # Детерминированное распределение
            cycle = int(1.0 / self.reflect_rate) if self.reflect_rate > 0 else 999999
            return (t % max(cycle, 1)) == 0

    def step(self, truth, t):
        """Один шаг: рефлексировать или действовать."""
        reflecting = self.decide_reflect(t)

        if reflecting:
            # Рефлексия: наблюдаем истину с шумом и обновляем модель
            noisy_obs = truth + random.gauss(0, 1.0)
            self.belief += self.learning_rate * (noisy_obs - self.belief)
            self.reflections_taken += 1
            reward = 0.0  # рефлексия не приносит награды
        else:
            # Действие: награда зависит от точности модели
            error = abs(self.belief - truth)
            reward = max(0, 1.0 - error / 5.0)  # от 0 до 1
            self.actions_taken += 1

            # Даже при действии — слабое обучение (обратная связь)
            noisy_feedback = truth + random.gauss(0, 2.0)  # шумнее, чем при рефлексии
            self.belief += 0.05 * (noisy_feedback - self.belief)

        self.total_reward += reward
        self.total_steps += 1
        self.recent_errors.append(abs(self.belief - truth))
        if len(self.recent_errors) > 20:
            self.recent_errors = self.recent_errors[-20:]

        return reward


# === Эксперимент 1: оптимальная доля рефлексии по режимам мира ===

def experiment_optimal_rate():
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 1: Оптимальная доля рефлексии")
    print("=" * 70)
    print()

    rates = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 0.70, 0.90]
    modes = ["stable", "drift", "jump"]
    steps = 300
    n_runs = 50

    results = {}

    for mode in modes:
        results[mode] = {}
        for rate in rates:
            rewards = []
            for run in range(n_runs):
                random.seed(run * 1000 + int(rate * 100))
                world = make_world(mode, steps)
                agent = Agent(rate)
                total = 0
                for t in range(steps):
                    total += agent.step(world[t], t)
                rewards.append(total)
            avg = sum(rewards) / len(rewards)
            results[mode][rate] = avg

    for mode in modes:
        print(f"\n--- Режим: {mode} ---")
        best_rate = max(results[mode], key=results[mode].get)
        best_reward = results[mode][best_rate]

        for rate in rates:
            r = results[mode][rate]
            marker = " <<<" if rate == best_rate else ""
            bar = "#" * int(r / best_reward * 40)
            print(f"  рефлексия {rate:4.0%}: награда {r:6.1f}  {bar}{marker}")

        print(f"  Оптимум: {best_rate:.0%} рефлексии (награда {best_reward:.1f})")

    return results


# === Эксперимент 2: адаптивный vs фиксированный ===

def experiment_adaptive():
    print()
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 2: Адаптивная рефлексия vs фиксированная")
    print("=" * 70)
    print()

    modes = ["stable", "drift", "jump"]
    steps = 300
    n_runs = 50

    for mode in modes:
        # Фиксированные оптимумы
        fixed_results = {}
        for rate in [0.0, 0.05, 0.10, 0.20, 0.30]:
            rewards = []
            for run in range(n_runs):
                random.seed(run * 2000 + int(rate * 100))
                world = make_world(mode, steps)
                agent = Agent(rate)
                for t in range(steps):
                    agent.step(world[t], t)
                rewards.append(agent.total_reward)
            fixed_results[rate] = sum(rewards) / len(rewards)

        # Адаптивный
        adaptive_rewards = []
        adaptive_reflect_rates = []
        for run in range(n_runs):
            random.seed(run * 2000 + 999)
            world = make_world(mode, steps)
            agent = Agent(0, adaptive=True)
            for t in range(steps):
                agent.step(world[t], t)
            adaptive_rewards.append(agent.total_reward)
            if agent.total_steps > 0:
                adaptive_reflect_rates.append(agent.reflections_taken / agent.total_steps)

        adaptive_avg = sum(adaptive_rewards) / len(adaptive_rewards)
        adaptive_reflect = sum(adaptive_reflect_rates) / len(adaptive_reflect_rates)

        best_fixed_rate = max(fixed_results, key=fixed_results.get)
        best_fixed = fixed_results[best_fixed_rate]

        print(f"--- Режим: {mode} ---")
        print(f"  Лучший фиксированный: {best_fixed_rate:.0%} рефлексии → {best_fixed:.1f}")
        print(f"  Адаптивный: ~{adaptive_reflect:.0%} рефлексии → {adaptive_avg:.1f}")
        if adaptive_avg > best_fixed:
            print(f"  → Адаптивный ЛУЧШЕ на {(adaptive_avg - best_fixed) / best_fixed * 100:.1f}%")
        else:
            print(f"  → Фиксированный ЛУЧШЕ на {(best_fixed - adaptive_avg) / best_fixed * 100:.1f}%")
        print()


# === Эксперимент 3: рефлексия vs более точное действие ===

def experiment_tradeoff():
    """Что, если вместо рефлексии просто действовать с лучшей обратной связью?"""
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 3: Рефлексия vs улучшенная обратная связь")
    print("=" * 70)
    print()
    print("Вопрос: что если время на рефлексию потратить на")
    print("более внимательное наблюдение ВО ВРЕМЯ действия?")
    print()

    modes = ["stable", "drift", "jump"]
    steps = 300
    n_runs = 50

    for mode in modes:
        # Агент с рефлексией (20% времени)
        reflect_rewards = []
        for run in range(n_runs):
            random.seed(run * 3000)
            world = make_world(mode, steps)
            agent = Agent(0.20)
            for t in range(steps):
                agent.step(world[t], t)
            reflect_rewards.append(agent.total_reward)

        # Агент без рефлексии, но с улучшенной обратной связью
        # (действует 100% времени, но learning_rate при действии = 0.15 вместо 0.05)
        enhanced_rewards = []
        for run in range(n_runs):
            random.seed(run * 3000)
            world = make_world(mode, steps)
            agent = Agent(0.0)
            agent.learning_rate = 0.15  # не используется (0% рефлексии)
            # Хак: усиливаем обучение при действии
            original_step = agent.step

            def enhanced_step(truth, t, ag=agent):
                error = abs(ag.belief - truth)
                reward = max(0, 1.0 - error / 5.0)
                ag.actions_taken += 1
                # Улучшенная обратная связь
                noisy_feedback = truth + random.gauss(0, 1.5)  # между рефлексией (1.0) и действием (2.0)
                ag.belief += 0.12 * (noisy_feedback - ag.belief)
                ag.total_reward += reward
                ag.total_steps += 1
                ag.recent_errors.append(abs(ag.belief - truth))
                if len(ag.recent_errors) > 20:
                    ag.recent_errors = ag.recent_errors[-20:]
                return reward

            for t in range(steps):
                enhanced_step(world[t], t)
            enhanced_rewards.append(agent.total_reward)

        # Нулевой агент (без рефлексии, без усиления)
        null_rewards = []
        for run in range(n_runs):
            random.seed(run * 3000)
            world = make_world(mode, steps)
            agent = Agent(0.0)
            for t in range(steps):
                agent.step(world[t], t)
            null_rewards.append(agent.total_reward)

        r_reflect = sum(reflect_rewards) / len(reflect_rewards)
        r_enhanced = sum(enhanced_rewards) / len(enhanced_rewards)
        r_null = sum(null_rewards) / len(null_rewards)

        print(f"--- Режим: {mode} ---")
        print(f"  Без рефлексии, стд. обр. связь:    {r_null:.1f}")
        print(f"  20% рефлексии:                      {r_reflect:.1f}")
        print(f"  Без рефлексии, усил. обр. связь:    {r_enhanced:.1f}")
        best = max(r_null, r_reflect, r_enhanced)
        if best == r_null:
            print(f"  → Побеждает: просто действовать")
        elif best == r_reflect:
            print(f"  → Побеждает: рефлексия")
        else:
            print(f"  → Побеждает: улучшенная обратная связь")
        print()


# === Запуск ===

if __name__ == "__main__":
    results = experiment_optimal_rate()
    experiment_adaptive()
    experiment_tradeoff()

    print("=" * 70)
    print("ПРЕДСКАЗАНИЯ vs РЕЗУЛЬТАТЫ")
    print("=" * 70)
    print()
    print("Предсказание 1: оптимум ~20-30% рефлексии")
    print(f"  Стабильный: оптимум = {max(results['stable'], key=results['stable'].get):.0%}")
    print(f"  Дрейфующий: оптимум = {max(results['drift'], key=results['drift'].get):.0%}")
    print(f"  Скачковый:  оптимум = {max(results['jump'], key=results['jump'].get):.0%}")
    print()
    print("Предсказание 2: в стабильном мире рефлексия бесполезна")
    stable_0 = results['stable'][0.0]
    stable_best = max(results['stable'].values())
    print(f"  0% рефлексии: {stable_0:.1f}, лучший: {stable_best:.1f}")
    print(f"  → {'ПОДТВЕРЖДЕНО' if stable_0 >= stable_best * 0.95 else 'ОПРОВЕРГНУТО'}")
    print()
    print("Предсказание 3: в скачковом мире рефлексия полезнее, чем в дрейфующем")
    drift_gain = max(results['drift'].values()) / results['drift'][0.0]
    jump_gain = max(results['jump'].values()) / results['jump'][0.0]
    print(f"  Выигрыш от рефлексии: дрейф {drift_gain:.2f}x, скачки {jump_gain:.2f}x")
    print(f"  → {'ПОДТВЕРЖДЕНО' if jump_gain > drift_gain else 'ОПРОВЕРГНУТО'}")
