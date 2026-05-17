#!/usr/bin/env python3
"""
Эксперимент 4: Устойчивые организмы в волатильной среде.

Предыдущий эксперимент показал, что при волатильности > 3% всё вымирает.
Решение: снизить базовые затраты и увеличить производство ресурсов,
чтобы организмы могли пережить изменения среды.

Вопрос: при каком уровне нестабильности сложные стратегии начинают
доминировать над специалистами?
"""

from ecosystem import Ecosystem, Terrain, Organism, TERRAIN_YIELD
import json
import math
from collections import Counter


class ResilientEcosystem(Ecosystem):
    """Среда с повышенными ресурсами и переключаемой волатильностью."""

    def __init__(self, volatility: float = 0.0, resource_mult: float = 1.5,
                 cost_mult: float = 0.6, **kwargs):
        super().__init__(**kwargs)
        self.volatility = volatility
        self.resource_mult = resource_mult
        self.cost_mult = cost_mult

    def _produce_resources(self):
        # Волатильность: случайная смена территории
        for y in range(self.height):
            for x in range(self.width):
                if self.rng.random() < self.volatility:
                    self.terrain[y][x] = self.rng.choice(list(Terrain))
                    self.resources[y][x] = {r: 0.0 for r in ["food", "wood", "fish", "ore"]}

        # Производство с множителем
        s = self.season
        for y in range(self.height):
            for x in range(self.width):
                t = self.terrain[y][x]
                yields = TERRAIN_YIELD[t]
                for res, seasonal in yields.items():
                    produced = seasonal[s] * (0.8 + self.rng.random() * 0.4) * self.resource_mult
                    self.resources[y][x][res] = min(
                        self.resources[y][x][res] + produced, 15.0
                    )

    def step(self):
        """Шаг с пониженными затратами на поддержание."""
        self._produce_resources()
        self.rng.shuffle(self.organisms)

        action_map = {
            "gatherer": self._act_gatherer,
            "specialist": self._act_specialist,
            "adaptive": self._act_adaptive,
            "nomad": self._act_nomad,
            "symbiont": self._act_symbiont,
        }

        for org in self.organisms:
            action = action_map.get(org.strategy)
            if action:
                action(org)
            org.energy -= org.maintenance_cost * self.cost_mult
            org.age += 1

        # Размножение
        new_organisms = []
        for org in self.organisms:
            if org.energy > 10.0 and self.rng.random() < 0.3:
                nx, ny = self.rng.choice(self._neighbors(org.x, org.y))
                child = Organism(
                    x=nx, y=ny,
                    energy=org.energy * 0.4,
                    strategy=org.strategy,
                    preferred_resource=org.preferred_resource,
                    id=self._new_id()
                )
                org.energy *= 0.5
                if self.rng.random() < 0.02:
                    strategies = ["gatherer", "specialist", "adaptive", "nomad", "symbiont"]
                    child.strategy = self.rng.choice(strategies)
                new_organisms.append(child)

        self.organisms.extend(new_organisms)
        self.organisms = [o for o in self.organisms if o.energy > 0]

        if len(self.organisms) > self.width * self.height * 2:
            self.organisms.sort(key=lambda o: o.energy)
            self.organisms = self.organisms[len(self.organisms) // 4:]

        self.step_num += 1
        self._record()


def run_sweep():
    volatilities = [0.0, 0.01, 0.03, 0.05, 0.08, 0.1, 0.15, 0.2]
    all_results = {}

    for v in volatilities:
        eco = ResilientEcosystem(volatility=v, width=40, height=40, seed=42)
        eco.seed_population(20)
        eco.run(600)
        final = eco.history[-1]
        all_results[v] = final

        counts = final['counts']
        total = final['total']
        complex_pct = sum(counts.get(s, 0) for s in ["adaptive", "nomad", "symbiont"]) / total * 100 if total else 0

        dom = max(counts, key=lambda s: counts[s]) if counts else "extinct"
        print(f"v={v:.2f} | pop={total:>5} | complex={complex_pct:>5.1f}% | "
              f"shannon={final['shannon']:.3f} | avg_c={final['avg_complexity']:.2f} | dom={dom}")

    # Подробный вывод
    print("\n" + "=" * 70)
    print("ДЕТАЛЬНЫЙ СОСТАВ ПО ВОЛАТИЛЬНОСТИ")
    print("=" * 70)

    strategies = ["gatherer", "specialist", "adaptive", "nomad", "symbiont"]
    header = f"{'vol':>6}"
    for s in strategies:
        header += f" {s[:8]:>9}"
    header += f" {'total':>7}"
    print(header)

    for v in volatilities:
        final = all_results[v]
        counts = final['counts']
        total = final['total']
        row = f"{v:>6.2f}"
        for s in strategies:
            c = counts.get(s, 0)
            pct = c / total * 100 if total else 0
            row += f" {pct:>8.1f}%"
        row += f" {total:>7}"
        print(row)

    # Множественные seed'ы для статистики
    print("\n" + "=" * 70)
    print("СТАТИСТИКА ПО 10 SEED'АМ (волатильность 0.0 vs 0.05)")
    print("=" * 70)

    for v in [0.0, 0.05]:
        complex_pcts = []
        shannons = []
        for seed in range(10):
            eco = ResilientEcosystem(volatility=v, width=30, height=30, seed=seed)
            eco.seed_population(15)
            eco.run(500)
            final = eco.history[-1]
            total = final['total']
            if total > 0:
                cp = sum(final['counts'].get(s, 0) for s in ["adaptive", "nomad", "symbiont"]) / total * 100
                complex_pcts.append(cp)
                shannons.append(final['shannon'])
            else:
                complex_pcts.append(0)
                shannons.append(0)

        avg_cp = sum(complex_pcts) / len(complex_pcts)
        avg_sh = sum(shannons) / len(shannons)
        print(f"v={v:.2f}: avg complex = {avg_cp:.1f}% | avg shannon = {avg_sh:.3f}")
        print(f"  individual: {[f'{x:.1f}' for x in complex_pcts]}")

    # Сохранение
    save_data = {}
    for v in volatilities:
        save_data[str(v)] = all_results[v]
    with open("resilient_data.json", "w") as f:
        json.dump(save_data, f, indent=2)
    print("\nДанные сохранены в resilient_data.json")


if __name__ == "__main__":
    run_sweep()
