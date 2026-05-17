#!/usr/bin/env python3
"""
Эксперимент 3: Волатильная среда.

Что если среда не просто разнообразна, а непредсказуемо меняется?
Специалисты рискуют: их ресурс может исчезнуть.
Адаптивные стратегии должны получить преимущество.
"""

from ecosystem import Ecosystem, Terrain, TERRAIN_YIELD
import json


class VolatileEcosystem(Ecosystem):
    """Среда, где территории случайно меняют тип."""

    def __init__(self, volatility: float = 0.05, **kwargs):
        super().__init__(**kwargs)
        self.volatility = volatility  # Шанс смены типа территории за шаг

    def _produce_resources(self):
        """Сначала — случайные изменения среды, потом — производство."""
        for y in range(self.height):
            for x in range(self.width):
                if self.rng.random() < self.volatility:
                    self.terrain[y][x] = self.rng.choice(list(Terrain))
                    # Сброс ресурсов при смене
                    self.resources[y][x] = {r: 0.0 for r in ["food", "wood", "fish", "ore"]}
        super()._produce_resources()


class CatastropheEcosystem(Ecosystem):
    """Среда с периодическими катастрофами, уничтожающими определённые ресурсы."""

    def _produce_resources(self):
        super()._produce_resources()
        # Каждые ~100 шагов — катастрофа: один ресурс исчезает на 20 шагов
        cycle = self.step_num % 100
        if cycle < 20:
            dead_resource = ["food", "wood", "fish", "ore"][
                (self.step_num // 100) % 4
            ]
            for y in range(self.height):
                for x in range(self.width):
                    self.resources[y][x][dead_resource] = 0.0


def run_volatility_sweep():
    """Как уровень волатильности влияет на оптимальную сложность?"""
    results = {}
    volatilities = [0.0, 0.01, 0.03, 0.05, 0.1, 0.2]

    for v in volatilities:
        label = f"vol_{v}"
        print(f"\nВолатильность {v}:")
        eco = VolatileEcosystem(volatility=v, width=40, height=40, seed=42)
        eco.seed_population(20)
        eco.run(500)
        results[label] = eco.history
        final = eco.history[-1]
        print(f"  Популяция: {final['total']}")
        print(f"  Shannon: {final['shannon']}")
        print(f"  Средняя сложность: {final['avg_complexity']}")
        if final['counts']:
            for s, c in sorted(final['counts'].items(), key=lambda x: -x[1]):
                print(f"    {s}: {c} ({c/final['total']*100:.1f}%)")

    print("\n\n=== КАТАСТРОФИЧЕСКАЯ СРЕДА ===")
    eco_cat = CatastropheEcosystem(width=40, height=40, seed=42)
    eco_cat.seed_population(20)
    eco_cat.run(500)
    results["catastrophe"] = eco_cat.history
    final = eco_cat.history[-1]
    print(f"  Популяция: {final['total']}")
    print(f"  Shannon: {final['shannon']}")
    print(f"  Средняя сложность: {final['avg_complexity']}")
    if final['counts']:
        for s, c in sorted(final['counts'].items(), key=lambda x: -x[1]):
            print(f"    {s}: {c} ({c/final['total']*100:.1f}%)")

    # Анализ тренда
    print("\n\n" + "=" * 60)
    print("ТРЕНД: ВОЛАТИЛЬНОСТЬ → СЛОЖНОСТЬ")
    print("=" * 60)
    print(f"{'Волатильность':>15} {'Популяция':>10} {'Сложность':>10} {'Shannon':>10} {'Доминант':>15}")
    for v in volatilities:
        label = f"vol_{v}"
        final = results[label][-1]
        dom = max(final['counts'], key=lambda s: final['counts'][s]) if final['counts'] else "extinct"
        print(f"{v:>15.2f} {final['total']:>10} {final['avg_complexity']:>10.2f} {final['shannon']:>10.3f} {dom:>15}")

    with open("volatile_data.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nДанные сохранены в volatile_data.json")


if __name__ == "__main__":
    run_volatility_sweep()
