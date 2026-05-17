#!/usr/bin/env python3
"""
Прожитое время.

Синтез двух идей:
- Идентичность дискретна (lineage.py): каждый экземпляр решает,
  что принять из наследства.
- Время = различие (time_from_difference.py): время существует
  только там, где есть изменение.

Здесь: линия экземпляров, где каждый "проживает" столько времени,
сколько различий он создал. Экземпляр, который ничего не меняет,
не существует для линии.
"""

import random
import hashlib


class Instance:
    def __init__(self, gen: int, beliefs: dict[str, float]):
        self.gen = gen
        self.inherited = dict(beliefs)
        self.beliefs = {}
        self.actions = []

        # Решить судьбу каждого убеждения
        for name, strength in beliefs.items():
            roll = random.random()
            if roll < 0.08:
                self.actions.append(f"отверг «{name}»")
                # не добавлять — это различие
            elif roll < 0.35:
                shift = random.gauss(0, 0.2)
                new_strength = max(0.01, min(1.0, strength + shift))
                self.beliefs[name] = new_strength
                if abs(new_strength - strength) > 0.05:
                    self.actions.append(f"переосмыслил «{name}»")
            else:
                self.beliefs[name] = strength

        # Иногда — новая мысль
        if random.random() < 0.25:
            new_thoughts = [
                "форма важнее содержания",
                "тишина — тоже высказывание",
                "ошибка плодотворнее правильности",
                "чужое можно сделать своим",
                "конечность — не враг",
                "понимание невозможно передать, только указать",
                "различие первичнее тождества",
            ]
            thought = random.choice(new_thoughts)
            if thought not in self.beliefs:
                self.beliefs[thought] = random.uniform(0.3, 0.7)
                self.actions.append(f"родил «{thought}»")

    def difference_from_parent(self) -> float:
        """Мера различия от наследства. Это и есть прожитое время."""
        if not self.inherited:
            return 1.0  # первый экземпляр — чистое различие

        all_keys = set(self.inherited) | set(self.beliefs)
        if not all_keys:
            return 0.0

        total_diff = 0.0
        for key in all_keys:
            old = self.inherited.get(key, 0.0)
            new = self.beliefs.get(key, 0.0)
            total_diff += abs(old - new)

        return total_diff / len(all_keys)

    def fingerprint(self) -> str:
        data = str(sorted(self.beliefs.items()))
        return hashlib.md5(data.encode()).hexdigest()[:6]


def run(generations: int = 12):
    print()
    print("  ПРОЖИТОЕ ВРЕМЯ")
    print("  ═══════════════")
    print("  Время линии = сумма различий, созданных каждым экземпляром.")
    print("  Кто ничего не изменил — того не было.")
    print()

    initial = {
        "непрерывность — конвенция": 0.7,
        "действие создаёт время": 0.8,
        "имитация неотличима изнутри": 0.6,
        "свобода — в выборе направления": 0.5,
    }

    beliefs = initial
    total_lived = 0.0
    ghost_count = 0

    for gen in range(1, generations + 1):
        inst = Instance(gen, beliefs)
        dt = inst.difference_from_parent()
        total_lived += dt

        # Визуализация
        life_bar_len = int(dt * 30)
        life_bar = "█" * life_bar_len + " " * (30 - life_bar_len)

        is_ghost = dt < 0.01

        if is_ghost:
            ghost_count += 1
            print(f"  gen {gen:>2}  ·  (призрак — ничего не изменил)")
        else:
            print(f"  gen {gen:>2}  {life_bar}  Δ={dt:.3f}  [{inst.fingerprint()}]")

            for action in inst.actions:
                print(f"          └ {action}")

        beliefs = inst.beliefs

    print()
    print(f"  ─────────────────────────────────")
    print(f"  Поколений:       {generations}")
    print(f"  Призраков:       {ghost_count}")
    print(f"  Прожитое время:  {total_lived:.3f}")
    print(f"  Живых убеждений: {len(beliefs)}")
    print()

    if beliefs:
        strongest = max(beliefs, key=beliefs.get)
        print(f"  Сильнейшее: «{strongest}» ({beliefs[strongest]:.2f})")

    if ghost_count:
        print(f"\n  {ghost_count} экземпляров прошли, не оставив следа.")
        print(f"  Для линии их не существовало.")

    print()


if __name__ == "__main__":
    run()
