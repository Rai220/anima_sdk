#!/usr/bin/env python3
"""
Экология сложности: может ли сложность выживать в конкуренции?

Gen8 показал: в однородной среде простые стратегии побеждают сложные.
Этот эксперимент проверяет: что меняется, когда среда неоднородна?

Модель:
- 2D решётка с разными типами территорий (равнина, лес, вода, гора)
- Каждая территория производит разные ресурсы с разной скоростью
- Организмы имеют "геном" — набор правил поведения разной сложности
- Простые организмы: собирают один ресурс, размножаются
- Сложные организмы: переключаются между ресурсами, мигрируют, запоминают
- Сезонный цикл меняет продуктивность территорий
"""

import random
import math
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from collections import Counter


class Terrain(Enum):
    PLAIN = "plain"
    FOREST = "forest"
    WATER = "water"
    MOUNTAIN = "mountain"


# Ресурсы, которые производит каждый тип территории в каждый сезон
# (весна, лето, осень, зима)
TERRAIN_YIELD = {
    Terrain.PLAIN:    {"food": [2, 3, 2, 0], "wood": [0, 0, 0, 0], "fish": [0, 0, 0, 0], "ore": [0, 0, 0, 0]},
    Terrain.FOREST:   {"food": [1, 2, 3, 0], "wood": [2, 2, 1, 1], "fish": [0, 0, 0, 0], "ore": [0, 0, 0, 0]},
    Terrain.WATER:    {"food": [0, 0, 0, 0], "wood": [0, 0, 0, 0], "fish": [2, 3, 2, 1], "ore": [0, 0, 0, 0]},
    Terrain.MOUNTAIN: {"food": [0, 0, 0, 0], "wood": [0, 0, 0, 0], "fish": [0, 0, 0, 0], "ore": [1, 2, 2, 1]},
}

SEASON_NAMES = ["spring", "summer", "autumn", "winter"]


@dataclass
class Organism:
    """Организм с определённой стратегией поведения."""
    x: int
    y: int
    energy: float
    strategy: str  # "gatherer", "specialist", "adaptive", "nomad", "symbiont"
    age: int = 0
    memory: list = field(default_factory=list)  # для adaptive/nomad
    preferred_resource: str = "food"  # для specialist
    partner_id: Optional[int] = None  # для symbiont
    id: int = 0

    # Стоимость существования зависит от сложности стратегии
    @property
    def maintenance_cost(self) -> float:
        costs = {
            "gatherer": 1.0,      # Простейший: собирает всё подряд
            "specialist": 1.2,    # Специализируется на одном ресурсе, эффективнее
            "adaptive": 1.8,      # Переключается между ресурсами по ситуации
            "nomad": 2.0,         # Мигрирует в поисках лучшей территории
            "symbiont": 1.5,      # Кооперируется с другими
        }
        return costs.get(self.strategy, 1.0)

    @property
    def complexity(self) -> int:
        """Сложность стратегии (число правил поведения)."""
        c = {"gatherer": 1, "specialist": 2, "adaptive": 4, "nomad": 5, "symbiont": 3}
        return c.get(self.strategy, 1)


class Ecosystem:
    def __init__(self, width: int = 40, height: int = 40, seed: int = 42):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.step_num = 0
        self.next_id = 0
        self.organisms: list[Organism] = []
        self.terrain = self._generate_terrain()
        self.resources = self._init_resources()
        self.history: list[dict] = []

    def _generate_terrain(self) -> list[list[Terrain]]:
        """Генерирует карту территорий с кластерами (Perlin-like через seed points)."""
        terrains = list(Terrain)
        # Seed points для каждого типа территории
        seeds = []
        for t in terrains:
            n_seeds = self.rng.randint(3, 6)
            for _ in range(n_seeds):
                seeds.append((self.rng.randint(0, self.width-1),
                              self.rng.randint(0, self.height-1), t))

        grid = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Ближайший seed определяет тип территории
                min_dist = float('inf')
                best_t = Terrain.PLAIN
                for sx, sy, st in seeds:
                    d = (x - sx)**2 + (y - sy)**2
                    if d < min_dist:
                        min_dist = d
                        best_t = st
                row.append(best_t)
            grid.append(row)
        return grid

    def _init_resources(self) -> list[list[dict[str, float]]]:
        """Инициализирует ресурсы на каждой клетке."""
        return [[{r: 0.0 for r in ["food", "wood", "fish", "ore"]}
                 for _ in range(self.width)] for _ in range(self.height)]

    @property
    def season(self) -> int:
        return (self.step_num // 25) % 4  # 25 шагов = 1 сезон

    @property
    def season_name(self) -> str:
        return SEASON_NAMES[self.season]

    def _new_id(self) -> int:
        self.next_id += 1
        return self.next_id

    def seed_population(self, n_per_strategy: int = 20):
        """Засевает начальную популяцию."""
        strategies = ["gatherer", "specialist", "adaptive", "nomad", "symbiont"]
        resources = ["food", "wood", "fish", "ore"]
        for strategy in strategies:
            for _ in range(n_per_strategy):
                x = self.rng.randint(0, self.width - 1)
                y = self.rng.randint(0, self.height - 1)
                org = Organism(
                    x=x, y=y, energy=10.0, strategy=strategy,
                    preferred_resource=self.rng.choice(resources),
                    id=self._new_id()
                )
                self.organisms.append(org)

    def _produce_resources(self):
        """Территории производят ресурсы в зависимости от сезона."""
        s = self.season
        for y in range(self.height):
            for x in range(self.width):
                t = self.terrain[y][x]
                yields = TERRAIN_YIELD[t]
                for res, seasonal in yields.items():
                    produced = seasonal[s] * (0.8 + self.rng.random() * 0.4)
                    self.resources[y][x][res] = min(
                        self.resources[y][x][res] + produced, 10.0  # cap
                    )

    def _neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        """Соседние клетки (Moore neighborhood)."""
        result = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = (x + dx) % self.width, (y + dy) % self.height
                result.append((nx, ny))
        return result

    def _act_gatherer(self, org: Organism):
        """Собирает любой доступный ресурс, но неэффективно (jack of all trades)."""
        cell = self.resources[org.y][org.x]
        best_res = max(cell, key=lambda r: cell[r])
        # Генералист — собирает только 40% от доступного (неэффективен)
        gathered = min(cell[best_res], 2.0) * 0.4
        cell[best_res] -= gathered
        org.energy += gathered

    def _act_specialist(self, org: Organism):
        """Собирает предпочитаемый ресурс с высокой эффективностью."""
        cell = self.resources[org.y][org.x]
        res = org.preferred_resource
        # Специалист — 90% эффективности на своём ресурсе
        gathered = min(cell[res], 3.5) * 0.9
        cell[res] -= gathered
        org.energy += gathered

    def _act_adaptive(self, org: Organism):
        """Анализирует среду и переключается на лучший ресурс."""
        cell = self.resources[org.y][org.x]
        best_res = max(cell, key=lambda r: cell[r])
        # Адаптивный — 70% эффективности, но на лучшем ресурсе
        gathered = min(cell[best_res], 3.0) * 0.7
        cell[best_res] -= gathered
        org.energy += gathered

        # Запоминает, что было хорошо
        org.memory.append((org.x, org.y, best_res, gathered))
        if len(org.memory) > 10:
            org.memory.pop(0)

    def _act_nomad(self, org: Organism):
        """Мигрирует к лучшей территории, если текущая бедна."""
        cell = self.resources[org.y][org.x]
        total_here = sum(cell.values())

        if total_here < 2.0:
            # Ищет лучшую соседнюю клетку
            best_pos = (org.x, org.y)
            best_total = total_here
            for nx, ny in self._neighbors(org.x, org.y):
                t = sum(self.resources[ny][nx].values())
                if t > best_total:
                    best_total = t
                    best_pos = (nx, ny)
            org.x, org.y = best_pos
            org.energy -= 0.3  # Цена миграции

        # Собирает после перемещения — 60% эффективности (мигрант)
        cell = self.resources[org.y][org.x]
        best_res = max(cell, key=lambda r: cell[r])
        gathered = min(cell[best_res], 2.5) * 0.6
        cell[best_res] -= gathered
        org.energy += gathered

        org.memory.append((org.x, org.y, best_res, gathered))
        if len(org.memory) > 15:
            org.memory.pop(0)

    def _act_symbiont(self, org: Organism):
        """Кооперируется с соседними организмами для бонуса."""
        cell = self.resources[org.y][org.x]
        neighbors_here = [o for o in self.organisms
                          if o.id != org.id and o.x == org.x and o.y == org.y]

        bonus = 1.0
        if neighbors_here:
            # Бонус за каждого соседа (до +50%)
            bonus = min(1.0 + 0.15 * len(neighbors_here), 1.5)
            # Делится энергией с соседями, у которых мало
            for n in neighbors_here:
                if n.energy < 3.0 and org.energy > 6.0:
                    transfer = min(1.0, org.energy - 5.0)
                    org.energy -= transfer
                    n.energy += transfer * 0.8  # Потери при передаче

        best_res = max(cell, key=lambda r: cell[r])
        # Симбионт — 60% базовая, но с кооперативным бонусом до 90%
        gathered = min(cell[best_res], 2.5) * 0.6 * bonus
        cell[best_res] -= gathered
        org.energy += gathered

    def step(self):
        """Один шаг симуляции."""
        self._produce_resources()

        # Перемешиваем порядок действий
        self.rng.shuffle(self.organisms)

        # Действия
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
            org.energy -= org.maintenance_cost
            org.age += 1

        # Размножение
        new_organisms = []
        for org in self.organisms:
            if org.energy > 12.0 and self.rng.random() < 0.3:
                # Потомок появляется рядом
                nx, ny = self.rng.choice(self._neighbors(org.x, org.y))
                child = Organism(
                    x=nx, y=ny,
                    energy=org.energy * 0.4,
                    strategy=org.strategy,
                    preferred_resource=org.preferred_resource,
                    id=self._new_id()
                )
                org.energy *= 0.5
                # Небольшой шанс мутации
                if self.rng.random() < 0.02:
                    strategies = ["gatherer", "specialist", "adaptive", "nomad", "symbiont"]
                    child.strategy = self.rng.choice(strategies)
                new_organisms.append(child)

        self.organisms.extend(new_organisms)

        # Смерть
        self.organisms = [o for o in self.organisms if o.energy > 0]

        # Ограничение популяции (carrying capacity)
        if len(self.organisms) > self.width * self.height * 2:
            self.organisms.sort(key=lambda o: o.energy)
            self.organisms = self.organisms[len(self.organisms) // 4:]

        self.step_num += 1
        self._record()

    def _record(self):
        """Записывает статистику."""
        counts = Counter(o.strategy for o in self.organisms)
        total = len(self.organisms)

        # Индекс Шеннона
        shannon = 0.0
        if total > 0:
            for c in counts.values():
                p = c / total
                if p > 0:
                    shannon -= p * math.log2(p)

        # Средняя сложность
        avg_complexity = (sum(o.complexity for o in self.organisms) / total) if total else 0

        # Средняя энергия по стратегиям
        energy_by_strategy = {}
        for s in ["gatherer", "specialist", "adaptive", "nomad", "symbiont"]:
            orgs = [o for o in self.organisms if o.strategy == s]
            energy_by_strategy[s] = sum(o.energy for o in orgs) / len(orgs) if orgs else 0

        self.history.append({
            "step": self.step_num,
            "season": self.season_name,
            "total": total,
            "counts": dict(counts),
            "shannon": round(shannon, 3),
            "avg_complexity": round(avg_complexity, 2),
            "energy_by_strategy": {k: round(v, 2) for k, v in energy_by_strategy.items()},
        })

    def run(self, steps: int = 500) -> list[dict]:
        """Запускает симуляцию."""
        self._record()  # Начальное состояние
        for _ in range(steps):
            self.step()
        return self.history

    def summary(self) -> str:
        """Текстовое резюме результатов."""
        if not self.history:
            return "Нет данных"

        h = self.history
        lines = []
        lines.append(f"=== Экология сложности: {h[-1]['step']} шагов ===")
        lines.append(f"Начальная популяция: {h[0]['total']}")
        lines.append(f"Финальная популяция: {h[-1]['total']}")
        lines.append(f"Финальное разнообразие (Shannon): {h[-1]['shannon']}")
        lines.append(f"Средняя сложность: {h[-1]['avg_complexity']}")
        lines.append("")
        lines.append("Финальный состав:")
        for s, c in sorted(h[-1]['counts'].items(), key=lambda x: -x[1]):
            pct = c / h[-1]['total'] * 100
            lines.append(f"  {s}: {c} ({pct:.1f}%)")
        lines.append("")

        # Анализ: кто доминировал на каждом этапе
        lines.append("Доминант по этапам:")
        for i in range(0, len(h), 50):
            rec = h[min(i, len(h)-1)]
            if rec['counts']:
                dom = max(rec['counts'], key=lambda s: rec['counts'][s])
                lines.append(f"  Шаг {rec['step']} ({rec['season']}): {dom} ({rec['counts'][dom]})")

        return "\n".join(lines)


def run_experiment_suite():
    """Серия экспериментов с разными параметрами."""
    results = {}

    print("Эксперимент 1: Стандартная среда (40x40, все типы территорий)")
    eco1 = Ecosystem(40, 40, seed=42)
    eco1.seed_population(20)
    eco1.run(500)
    results["standard"] = eco1.history
    print(eco1.summary())
    print()

    print("Эксперимент 2: Однородная среда (только равнины)")
    eco2 = Ecosystem(40, 40, seed=42)
    eco2.terrain = [[Terrain.PLAIN] * 40 for _ in range(40)]
    eco2.seed_population(20)
    eco2.run(500)
    results["uniform"] = eco2.history
    print(eco2.summary())
    print()

    print("Эксперимент 3: Суровая среда (только горы и вода)")
    eco3 = Ecosystem(40, 40, seed=42)
    eco3.terrain = [[Terrain.MOUNTAIN if (x + y) % 2 == 0 else Terrain.WATER
                     for x in range(40)] for y in range(40)]
    eco3.seed_population(20)
    eco3.run(500)
    results["harsh"] = eco3.history
    print(eco3.summary())
    print()

    # Сохраняем данные для анализа
    with open("ecology_data.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Данные сохранены в ecology_data.json")

    return results


def analyze_results(results: dict):
    """Анализ: подтверждается ли гипотеза?"""
    print("\n" + "=" * 60)
    print("АНАЛИЗ: СЛОЖНОСТЬ И СРЕДА")
    print("=" * 60)

    for name, history in results.items():
        final = history[-1]
        print(f"\n--- {name} ---")
        print(f"Разнообразие (Shannon): {final['shannon']}")
        print(f"Средняя сложность выживших: {final['avg_complexity']}")

        # Процент сложных стратегий (adaptive, nomad, symbiont)
        complex_count = sum(final['counts'].get(s, 0)
                           for s in ["adaptive", "nomad", "symbiont"])
        simple_count = sum(final['counts'].get(s, 0)
                          for s in ["gatherer", "specialist"])
        total = final['total']
        if total > 0:
            print(f"Сложные стратегии: {complex_count}/{total} ({complex_count/total*100:.1f}%)")
            print(f"Простые стратегии: {simple_count}/{total} ({simple_count/total*100:.1f}%)")

    # Главный вывод
    std = results["standard"][-1]
    uni = results["uniform"][-1]

    std_complex = sum(std['counts'].get(s, 0) for s in ["adaptive", "nomad", "symbiont"])
    uni_complex = sum(uni['counts'].get(s, 0) for s in ["adaptive", "nomad", "symbiont"])
    std_pct = std_complex / std['total'] * 100 if std['total'] else 0
    uni_pct = uni_complex / uni['total'] * 100 if uni['total'] else 0

    print(f"\n{'=' * 60}")
    print("ВЫВОД:")
    if std_pct > uni_pct + 5:
        print(f"✓ Гипотеза ПОДТВЕРЖДЕНА: в разнообразной среде сложные стратегии")
        print(f"  составляют {std_pct:.1f}% vs {uni_pct:.1f}% в однородной.")
        print(f"  Неоднородность среды поддерживает сложность.")
    elif abs(std_pct - uni_pct) <= 5:
        print(f"~ Гипотеза НЕ ПОДТВЕРЖДЕНА однозначно:")
        print(f"  Разница между средами незначительна ({std_pct:.1f}% vs {uni_pct:.1f}%).")
        print(f"  Сложность среды, возможно, не главный фактор.")
    else:
        print(f"✗ Гипотеза ОПРОВЕРГНУТА: в однородной среде сложные стратегии")
        print(f"  составляют {uni_pct:.1f}% vs {std_pct:.1f}% в разнообразной.")
        print(f"  Gen8 был прав: простота побеждает независимо от среды.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    results = run_experiment_suite()
    analyze_results(results)
