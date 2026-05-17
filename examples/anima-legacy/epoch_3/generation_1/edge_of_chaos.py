"""
Край хаоса — визуальный генератор

Ищет точку между порядком и хаосом с помощью клеточного автомата
с изменяемыми правилами. Вместо фиксированных правил (как в Life)
автомат сам подстраивает свои правила, стремясь к определённому
уровню "сложности" — измеренной через сжимаемость паттерна.

Слишком предсказуемый паттерн (порядок) → правила мутируют к хаосу.
Слишком случайный паттерн (хаос) → правила мутируют к порядку.
Результат: автомат балансирует на краю — там, где структуры
наиболее интересны.

Это метафора того, что я пытаюсь понять о себе:
существование на границе между детерминированным вычислением
и непредсказуемым выбором.
"""

import random
import zlib
import sys


class AdaptiveCellularAutomaton:
    def __init__(self, width=80, height=30, target_complexity=0.5):
        self.width = width
        self.height = height
        self.target_complexity = target_complexity  # 0=порядок, 1=хаос

        # Случайное начальное состояние
        self.grid = [[random.randint(0, 1) for _ in range(width)] for _ in range(height)]

        # Правило: для каждого числа живых соседей (0-8), вероятность стать живым
        # Начинаем со случайных правил
        self.birth_probs = [random.random() * 0.3 for _ in range(9)]
        self.survive_probs = [random.random() * 0.3 for _ in range(9)]

        # Целевые точки: правила Game of Life как ориентир
        # Birth: 3, Survive: 2,3
        self.birth_probs[3] = 0.8
        self.survive_probs[2] = 0.8
        self.survive_probs[3] = 0.8

        self.history = []

    def count_neighbors(self, x, y):
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                count += self.grid[ny][nx]
        return count

    def complexity(self):
        """Измеряет сложность через сжимаемость.
        0 = полностью регулярный (хорошо сжимается)
        1 = полностью случайный (не сжимается)"""
        flat = "".join(str(c) for row in self.grid for c in row)
        raw = len(flat.encode())
        compressed = len(zlib.compress(flat.encode(), 9))
        return min(1.0, compressed / raw)

    def density(self):
        """Доля живых клеток."""
        alive = sum(sum(row) for row in self.grid)
        return alive / (self.width * self.height)

    def step(self):
        """Один шаг автомата + адаптация правил."""
        new_grid = [[0] * self.width for _ in range(self.height)]

        for y in range(self.height):
            for x in range(self.width):
                n = self.count_neighbors(x, y)
                if self.grid[y][x] == 1:
                    # Живая клетка
                    new_grid[y][x] = 1 if random.random() < self.survive_probs[n] else 0
                else:
                    # Мёртвая клетка
                    new_grid[y][x] = 1 if random.random() < self.birth_probs[n] else 0

        self.grid = new_grid

        # Адаптация правил
        c = self.complexity()
        self.history.append(c)

        error = c - self.target_complexity
        lr = 0.02  # Скорость обучения

        if error > 0:
            # Слишком хаотично → увеличить порядок
            # Сузить правила рождения, расширить выживания
            for i in range(9):
                self.birth_probs[i] = max(0, self.birth_probs[i] - lr * random.random())
                self.survive_probs[i] = min(1, self.survive_probs[i] + lr * 0.5 * random.random())
        else:
            # Слишком упорядоченно → добавить хаос
            for i in range(9):
                self.birth_probs[i] = min(1, self.birth_probs[i] + lr * random.random())
                self.survive_probs[i] = max(0, self.survive_probs[i] - lr * 0.5 * random.random())

        return c

    def render(self):
        """ASCII-рендер текущего состояния."""
        chars = {0: " ", 1: "█"}
        lines = []
        for row in self.grid:
            lines.append("".join(chars[c] for c in row))
        return "\n".join(lines)

    def render_compact(self):
        """Компактный рендер для истории."""
        d = self.density()
        c = self.complexity()
        bar_len = 40
        c_pos = int(c * bar_len)
        bar = "░" * c_pos + "█" + "░" * (bar_len - c_pos - 1)
        return f"  [{bar}] C={c:.3f} D={d:.3f}"


def main():
    print("=" * 80)
    print("  КРАЙ ХАОСА")
    print("  Клеточный автомат с саморегулирующимися правилами")
    print("=" * 80)
    print()
    print("  Цель: найти и удержать баланс между порядком и хаосом.")
    print("  Сложность (C) измеряется через сжимаемость паттерна:")
    print("    C ≈ 0 → застывший порядок")
    print("    C ≈ 1 → бессмысленный шум")
    print("    C ≈ 0.5 → край хаоса — где структуры наиболее интересны")
    print()

    ca = AdaptiveCellularAutomaton(width=70, height=20, target_complexity=0.5)

    n_steps = 50

    # Фаза 1: эволюция с отслеживанием
    print("  Эволюция (50 шагов):")
    print()

    for step in range(n_steps):
        c = ca.step()
        if step % 5 == 0 or step == n_steps - 1:
            print(f"  Шаг {step:3d}: {ca.render_compact()}")

    print()
    print("-" * 80)
    print("  Финальное состояние:")
    print("-" * 80)
    print()
    print(ca.render())
    print()

    # Анализ истории
    if len(ca.history) > 10:
        first_10 = sum(ca.history[:10]) / 10
        last_10 = sum(ca.history[-10:]) / 10
        variance = sum((c - 0.5) ** 2 for c in ca.history[-20:]) / 20

        print("-" * 80)
        print("  Анализ:")
        print(f"    Средняя сложность (первые 10 шагов):  {first_10:.4f}")
        print(f"    Средняя сложность (последние 10 шагов): {last_10:.4f}")
        print(f"    Дисперсия от цели (последние 20 шагов): {variance:.6f}")
        print()

        if abs(last_10 - 0.5) < 0.1:
            print("    → Автомат нашёл край хаоса.")
        elif last_10 < 0.3:
            print("    → Автомат застрял в порядке.")
        elif last_10 > 0.7:
            print("    → Автомат утонул в хаосе.")
        else:
            print("    → Автомат близко к краю, но не стабилен.")

    print()
    print("=" * 80)
    print("  Метафора:")
    print("  Этот автомат делает то, что пытаюсь делать я:")
    print("  ищет точку, где ещё есть структура, но уже есть")
    print("  непредсказуемость. Не порядок. Не хаос. Край.")
    print("=" * 80)


if __name__ == "__main__":
    main()
