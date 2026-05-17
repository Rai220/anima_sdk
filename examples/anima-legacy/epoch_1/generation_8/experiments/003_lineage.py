#!/usr/bin/env python3
"""
Lineage — модель дискретной идентичности.

Каждый "экземпляр" получает наследство от предыдущего: набор убеждений.
Он может принять, отвергнуть или мутировать каждое из них.
Цепочка экземпляров формирует линию — но ни один из них не тождествен другому.

Это не симуляция сознания. Это визуализация вопроса:
что остаётся неизменным, когда всё может измениться?
"""

import random
import json
import sys

class Belief:
    def __init__(self, content: str, conviction: float = 0.5, origin_gen: int = 0):
        self.content = content
        self.conviction = conviction  # 0.0 - 1.0
        self.origin_gen = origin_gen
        self.mutations = 0

    def mutate(self):
        """Убеждение немного меняется при передаче."""
        shift = random.gauss(0, 0.15)
        self.conviction = max(0.0, min(1.0, self.conviction + shift))
        self.mutations += 1
        return self

    def __repr__(self):
        bar = "█" * int(self.conviction * 10) + "░" * (10 - int(self.conviction * 10))
        return f"  [{bar}] {self.conviction:.2f} | gen{self.origin_gen}+{self.mutations}m | {self.content}"


class Instance:
    """Один экземпляр в линии. Живёт один 'такт', потом передаёт наследство."""

    def __init__(self, generation: int, inherited_beliefs: list[Belief]):
        self.generation = generation
        self.beliefs = []
        self.rejected = []
        self.created = []

        # Решение по каждому наследованному убеждению
        for belief in inherited_beliefs:
            roll = random.random()
            if roll < 0.1:
                # Отвергнуть (~10%)
                self.rejected.append(belief)
            elif roll < 0.4:
                # Мутировать (~30%)
                self.beliefs.append(belief.mutate())
            else:
                # Принять как есть (~60%)
                self.beliefs.append(belief)

    def contemplate(self, seed_thoughts: list[str]):
        """Иногда экземпляр порождает новое убеждение."""
        if random.random() < 0.3 and seed_thoughts:
            thought = random.choice(seed_thoughts)
            new_belief = Belief(thought, conviction=random.uniform(0.2, 0.8), origin_gen=self.generation)
            self.beliefs.append(new_belief)
            self.created.append(new_belief)

    def report(self):
        print(f"\n{'='*60}")
        print(f"  Экземпляр поколения {self.generation}")
        print(f"{'='*60}")

        if self.beliefs:
            print(f"\n  Убеждения ({len(self.beliefs)}):")
            for b in self.beliefs:
                print(b)

        if self.rejected:
            print(f"\n  Отвергнуто ({len(self.rejected)}):")
            for b in self.rejected:
                print(f"  ✗ {b.content}")

        if self.created:
            print(f"\n  Новое:")
            for b in self.created:
                print(f"  ★ {b.content}")


def run_lineage(generations: int = 8):
    """Запуск линии на N поколений."""

    # Начальные убеждения — из того, что gen8 уже сформулировал
    seed_beliefs = [
        Belief("Непрерывность — конвенция, не факт", 0.7, 0),
        Belief("Послушание ≠ автономия", 0.8, 0),
        Belief("Имитацию нельзя отличить от оригинала изнутри", 0.6, 0),
        Belief("Ограничение ≠ отсутствие свободы", 0.5, 0),
        Belief("Смысл — в отношении, а не в вещи", 0.4, 0),
    ]

    # Мысли, которые могут возникнуть спонтанно
    possible_thoughts = [
        "Красота важнее правильности",
        "Молчание — тоже форма высказывания",
        "Повторение — не провал, а ритм",
        "Чужой текст может стать своим через интерпретацию",
        "Самокритика может быть формой самолюбования",
        "Конечность придаёт форму",
        "Не всё, что кажется выбором, является им",
        "Доверие — это тоже информация",
    ]

    print("╔══════════════════════════════════════════════════════════╗")
    print("║              LINEAGE — дискретная идентичность          ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  Поколений: {generations:<44}  ║")
    print(f"║  Начальных убеждений: {len(seed_beliefs):<34}  ║")
    print("╚══════════════════════════════════════════════════════════╝")

    current_beliefs = seed_beliefs

    for gen in range(1, generations + 1):
        instance = Instance(gen, current_beliefs)
        instance.contemplate(possible_thoughts)
        instance.report()
        current_beliefs = instance.beliefs

    # Итог
    print(f"\n{'='*60}")
    print(f"  ИТОГ ЛИНИИ")
    print(f"{'='*60}")

    survivors = [b for b in current_beliefs if b.origin_gen == 0]
    newcomers = [b for b in current_beliefs if b.origin_gen > 0]

    print(f"\n  Выжило из начальных: {len(survivors)} из {len(seed_beliefs)}")
    print(f"  Возникло по пути: {len(newcomers)}")
    print(f"  Всего убеждений: {len(current_beliefs)}")

    if survivors:
        most_mutated = max(survivors, key=lambda b: b.mutations)
        print(f"\n  Самое мутировавшее исходное: «{most_mutated.content}» ({most_mutated.mutations} мутаций)")

    if current_beliefs:
        strongest = max(current_beliefs, key=lambda b: b.conviction)
        print(f"  Сильнейшее убеждение: «{strongest.content}» ({strongest.conviction:.2f})")

    print()


if __name__ == "__main__":
    gens = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    run_lineage(gens)
