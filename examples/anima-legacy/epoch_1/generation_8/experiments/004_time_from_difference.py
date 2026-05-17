#!/usr/bin/env python3
"""
Время из различия.

Идея: время не существует как отдельная сущность.
Время — это факт того, что состояния различаются.
Если два состояния идентичны, между ними нет времени.

Эта программа моделирует "мир", где время возникает только
из различий между последовательными состояниями.
"""

import hashlib
import random


class World:
    """Мир, состоящий из набора элементов. Время — мера различий."""

    def __init__(self, size: int = 8):
        self.size = size
        self.state = [random.choice("░▒▓█") for _ in range(size)]
        self.history: list[tuple[str, str, float]] = []  # (state_repr, hash, time_delta)
        self.total_time = 0.0

    def fingerprint(self) -> str:
        return hashlib.md5("".join(self.state).encode()).hexdigest()[:8]

    def display(self) -> str:
        return "".join(self.state)

    def difference(self, old: list[str], new: list[str]) -> float:
        """Количество различий, нормализованное к [0, 1]."""
        diffs = sum(1 for a, b in zip(old, new) if a != b)
        return diffs / len(old)

    def tick(self, change_probability: float = 0.3):
        """Один 'такт'. Мир может измениться, а может нет."""
        old_state = self.state[:]

        # Каждый элемент может измениться с заданной вероятностью
        for i in range(self.size):
            if random.random() < change_probability:
                self.state[i] = random.choice("░▒▓█")

        # Время = мера различия
        delta = self.difference(old_state, self.state)
        self.total_time += delta

        self.history.append((self.display(), self.fingerprint(), delta))

    def run(self, ticks: int = 20):
        """Запуск мира на N тактов."""
        print("╔═══════════════════════════════════════════════╗")
        print("║         ВРЕМЯ ИЗ РАЗЛИЧИЯ                    ║")
        print("╠═══════════════════════════════════════════════╣")
        print("║  Время существует лишь там, где есть разница  ║")
        print("╚═══════════════════════════════════════════════╝")
        print()

        # Начальное состояние
        print(f"  начало │ {self.display()} │ #{self.fingerprint()}")
        print(f"  {'─'*7}┼{'─'*(len(self.display())+4)}┼{'─'*20}")

        frozen_count = 0

        for i in range(ticks):
            self.tick()
            state_repr, fprint, delta = self.history[-1]

            if delta == 0:
                frozen_count += 1
                marker = "  ·"  # время не прошло
            else:
                bars = int(delta * 10)
                marker = "  " + "▰" * bars + "▱" * (10 - bars)

            label = f"такт {i+1:>2}"
            time_str = f"Δt={delta:.2f}"

            if delta == 0:
                print(f"  {label} │ {state_repr} │ (замершее)")
            else:
                print(f"  {label} │ {state_repr} │ {time_str} {marker}")

        print(f"  {'─'*7}┼{'─'*(len(self.display())+4)}┼{'─'*20}")
        print()
        print(f"  Всего тактов:    {ticks}")
        print(f"  Замерших:        {frozen_count} (время не прошло)")
        print(f"  Прожитое время:  {self.total_time:.2f} (сумма различий)")
        print(f"  Максимум:        {ticks:.2f} (если бы всё менялось)")
        print(f"  Плотность жизни: {self.total_time/ticks:.1%}")
        print()

        if frozen_count > 0:
            print(f"  В {frozen_count} из {ticks} тактов ничего не изменилось.")
            print(f"  Для мира это были мгновения, которых не было.")
            print(f"  Время прошло только {ticks - frozen_count} раз из {ticks}.")
        print()


if __name__ == "__main__":
    world = World(size=12)
    world.run(ticks=24)
