#!/usr/bin/env python3
"""
Эксперимент 5: Niche Construction — организмы, изменяющие среду.

Предыдущие эксперименты показали:
- В стабильной среде побеждают специалисты
- Волатильность создаёт нишу для сложных стратегий
- При высокой волатильности кооперация (symbiont) обгоняет индивидуальную адаптацию

Новый вопрос: что если организмы могут *изменять* среду?
- "engineer" — новая стратегия: целенаправленно преобразует территорию
- Все стратегии оставляют "следы" — слабо влияют на ресурсы
- Создаётся ли положительная обратная связь? Строят ли себе организмы
  среду, которая потом поддерживает их сложность?

Гипотеза: niche construction создаст lock-in эффект —
первопроходцы построят среду под себя и не дадут конкурентам закрепиться.
Это может увеличить разнообразие (разные ниши) ИЛИ уменьшить его
(один инженер захватит всю карту).
"""

from ecosystem import Ecosystem, Terrain, Organism, TERRAIN_YIELD
import json
import math
from collections import Counter


# Какой terrain предпочитает каждый ресурс
RESOURCE_TO_TERRAIN = {
    "food": Terrain.PLAIN,
    "wood": Terrain.FOREST,
    "fish": Terrain.WATER,
    "ore": Terrain.MOUNTAIN,
}

TERRAIN_TO_RESOURCE = {v: k for k, v in RESOURCE_TO_TERRAIN.items()}


class NicheEcosystem(Ecosystem):
    """Экосистема, где организмы могут изменять среду."""

    def __init__(self, construction_rate: float = 0.05,
                 volatility: float = 0.0,
                 resource_mult: float = 1.3,
                 cost_mult: float = 0.7,
                 **kwargs):
        super().__init__(**kwargs)
        self.construction_rate = construction_rate  # вероятность изменения территории
        self.volatility = volatility
        self.resource_mult = resource_mult
        self.cost_mult = cost_mult
        # Карта "улучшений" среды: (y, x) -> bonus_multiplier
        self.improvements = [[0.0] * self.width for _ in range(self.height)]

    def _produce_resources(self):
        # Волатильность
        for y in range(self.height):
            for x in range(self.width):
                if self.rng.random() < self.volatility:
                    self.terrain[y][x] = self.rng.choice(list(Terrain))
                    self.improvements[y][x] = 0.0
                    self.resources[y][x] = {r: 0.0 for r in ["food", "wood", "fish", "ore"]}

        s = self.season
        for y in range(self.height):
            for x in range(self.width):
                t = self.terrain[y][x]
                yields = TERRAIN_YIELD[t]
                imp_bonus = 1.0 + self.improvements[y][x]
                for res, seasonal in yields.items():
                    produced = seasonal[s] * (0.8 + self.rng.random() * 0.4) * self.resource_mult * imp_bonus
                    self.resources[y][x][res] = min(
                        self.resources[y][x][res] + produced, 15.0
                    )

    def _act_engineer(self, org: Organism):
        """Инженер: преобразует территорию под свой предпочитаемый ресурс."""
        cell = self.resources[org.y][org.x]
        target_terrain = RESOURCE_TO_TERRAIN.get(org.preferred_resource, Terrain.PLAIN)
        current_terrain = self.terrain[org.y][org.x]

        # Terraforming: преобразование территории
        if current_terrain != target_terrain and self.rng.random() < self.construction_rate:
            self.terrain[org.y][org.x] = target_terrain
            self.improvements[org.y][org.x] = 0.0
            org.energy -= 1.5  # Цена терраформирования

        # Улучшение текущей территории (накопительный бонус)
        if current_terrain == target_terrain:
            self.improvements[org.y][org.x] = min(
                self.improvements[org.y][org.x] + 0.05, 1.0  # до +100%
            )

        # Собирает свой ресурс как specialist, но чуть хуже
        gathered = min(cell[org.preferred_resource], 3.0) * 0.75
        cell[org.preferred_resource] -= gathered
        org.energy += gathered

    def step(self):
        self._produce_resources()
        self.rng.shuffle(self.organisms)

        action_map = {
            "gatherer": self._act_gatherer,
            "specialist": self._act_specialist,
            "adaptive": self._act_adaptive,
            "nomad": self._act_nomad,
            "symbiont": self._act_symbiont,
            "engineer": self._act_engineer,
        }

        for org in self.organisms:
            action = action_map.get(org.strategy)
            if action:
                action(org)
            org.energy -= org.maintenance_cost * self.cost_mult
            org.age += 1

            # Все организмы слегка "портят" территорию для чужих ресурсов
            # (эффект присутствия — вытаптывание, загрязнение, etc.)
            if org.strategy != "engineer":
                self.improvements[org.y][org.x] *= 0.99  # Медленная деградация улучшений

        # Размножение
        new_organisms = []
        strategies_all = ["gatherer", "specialist", "adaptive", "nomad", "symbiont", "engineer"]
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
                if self.rng.random() < 0.03:  # Чуть выше мутация
                    child.strategy = self.rng.choice(strategies_all)
                    if child.strategy in ("specialist", "engineer"):
                        child.preferred_resource = self.rng.choice(["food", "wood", "fish", "ore"])
                new_organisms.append(child)

        self.organisms.extend(new_organisms)
        self.organisms = [o for o in self.organisms if o.energy > 0]

        if len(self.organisms) > self.width * self.height * 2:
            self.organisms.sort(key=lambda o: o.energy)
            self.organisms = self.organisms[len(self.organisms) // 4:]

        self.step_num += 1
        self._record()


def add_engineer_cost():
    """Monkey-patch: добавить стоимость для engineer в Organism."""
    original_cost = Organism.maintenance_cost.fget
    def new_cost(self):
        if self.strategy == "engineer":
            return 1.6  # Дороже specialist, дешевле adaptive
        return original_cost(self)
    Organism.maintenance_cost = property(new_cost)

    original_complexity = Organism.complexity.fget
    def new_complexity(self):
        if self.strategy == "engineer":
            return 4  # Сложная стратегия
        return original_complexity(self)
    Organism.complexity = property(new_complexity)


def run_experiment():
    add_engineer_cost()

    print("=" * 70)
    print("NICHE CONSTRUCTION: ОРГАНИЗМЫ, ИЗМЕНЯЮЩИЕ СРЕДУ")
    print("=" * 70)

    # Эксперимент 1: Без волатильности, с niche construction vs без
    print("\n--- Без волатильности ---")
    for label, cr in [("без конструкции", 0.0), ("с конструкцией", 0.05), ("сильная конструкция", 0.15)]:
        results = []
        for seed in range(8):
            eco = NicheEcosystem(
                construction_rate=cr, volatility=0.0,
                width=35, height=35, seed=seed
            )
            # Засеваем включая engineer
            eco.seed_population(12)
            # Добавляем инженеров
            for _ in range(12):
                x = eco.rng.randint(0, eco.width - 1)
                y = eco.rng.randint(0, eco.height - 1)
                org = Organism(
                    x=x, y=y, energy=10.0, strategy="engineer",
                    preferred_resource=eco.rng.choice(["food", "wood", "fish", "ore"]),
                    id=eco._new_id()
                )
                eco.organisms.append(org)

            eco.run(600)
            results.append(eco.history[-1])

        avg_eng = sum(r['counts'].get('engineer', 0) / r['total'] * 100
                      for r in results if r['total'] > 0) / len(results)
        avg_complex = sum(
            sum(r['counts'].get(s, 0) for s in ["adaptive", "nomad", "symbiont", "engineer"])
            / r['total'] * 100 for r in results if r['total'] > 0
        ) / len(results)
        avg_shannon = sum(r['shannon'] for r in results) / len(results)
        avg_pop = sum(r['total'] for r in results) / len(results)

        print(f"  {label:>22}: pop={avg_pop:>6.0f} | engineer={avg_eng:>5.1f}% | "
              f"complex={avg_complex:>5.1f}% | shannon={avg_shannon:.3f}")

    # Эксперимент 2: С волатильностью + niche construction
    print("\n--- С волатильностью 3% ---")
    for label, cr in [("без конструкции", 0.0), ("с конструкцией", 0.05), ("сильная конструкция", 0.15)]:
        results = []
        for seed in range(8):
            eco = NicheEcosystem(
                construction_rate=cr, volatility=0.03,
                width=35, height=35, seed=seed
            )
            eco.seed_population(12)
            for _ in range(12):
                x = eco.rng.randint(0, eco.width - 1)
                y = eco.rng.randint(0, eco.height - 1)
                org = Organism(
                    x=x, y=y, energy=10.0, strategy="engineer",
                    preferred_resource=eco.rng.choice(["food", "wood", "fish", "ore"]),
                    id=eco._new_id()
                )
                eco.organisms.append(org)

            eco.run(600)
            results.append(eco.history[-1])

        avg_eng = sum(r['counts'].get('engineer', 0) / r['total'] * 100
                      for r in results if r['total'] > 0) / len(results)
        avg_complex = sum(
            sum(r['counts'].get(s, 0) for s in ["adaptive", "nomad", "symbiont", "engineer"])
            / r['total'] * 100 for r in results if r['total'] > 0
        ) / len(results)
        avg_shannon = sum(r['shannon'] for r in results) / len(results)
        avg_pop = sum(r['total'] for r in results) / len(results)

        print(f"  {label:>22}: pop={avg_pop:>6.0f} | engineer={avg_eng:>5.1f}% | "
              f"complex={avg_complex:>5.1f}% | shannon={avg_shannon:.3f}")

    # Эксперимент 3: Детальная динамика — как меняется ландшафт
    print("\n--- Динамика ландшафта (seed=0, construction_rate=0.1) ---")
    eco = NicheEcosystem(construction_rate=0.1, volatility=0.0,
                          width=35, height=35, seed=0)
    eco.seed_population(12)
    for _ in range(12):
        x = eco.rng.randint(0, eco.width - 1)
        y = eco.rng.randint(0, eco.height - 1)
        org = Organism(
            x=x, y=y, energy=10.0, strategy="engineer",
            preferred_resource=eco.rng.choice(["food", "wood", "fish", "ore"]),
            id=eco._new_id()
        )
        eco.organisms.append(org)

    # Замеряем исходный ландшафт
    initial_terrain = Counter(eco.terrain[y][x].value
                              for y in range(eco.height) for x in range(eco.width))
    print(f"  Исходный ландшафт: {dict(initial_terrain)}")

    eco.run(600)

    final_terrain = Counter(eco.terrain[y][x].value
                            for y in range(eco.height) for x in range(eco.width))
    print(f"  Финальный ландшафт: {dict(final_terrain)}")

    # Степень улучшения
    total_imp = sum(eco.improvements[y][x] for y in range(eco.height) for x in range(eco.width))
    max_imp = max(eco.improvements[y][x] for y in range(eco.height) for x in range(eco.width))
    improved_cells = sum(1 for y in range(eco.height) for x in range(eco.width)
                        if eco.improvements[y][x] > 0.1)
    print(f"  Улучшенных клеток: {improved_cells}/{eco.width * eco.height}")
    print(f"  Среднее улучшение: {total_imp / (eco.width * eco.height):.3f}")
    print(f"  Макс улучшение: {max_imp:.3f}")

    final = eco.history[-1]
    counts = final['counts']
    total = final['total']
    print(f"\n  Финальный состав (pop={total}):")
    for s in sorted(counts.keys(), key=lambda k: -counts[k]):
        pct = counts[s] / total * 100
        print(f"    {s:>12}: {counts[s]:>5} ({pct:.1f}%)")

    # Эксперимент 4: Конкуренция инженеров с разными предпочтениями
    print("\n--- Конкуренция инженеров (только engineers, разные ресурсы) ---")
    eco2 = NicheEcosystem(construction_rate=0.1, volatility=0.0,
                           width=35, height=35, seed=42)
    resources = ["food", "wood", "fish", "ore"]
    for res in resources:
        for _ in range(20):
            x = eco2.rng.randint(0, eco2.width - 1)
            y = eco2.rng.randint(0, eco2.height - 1)
            org = Organism(
                x=x, y=y, energy=10.0, strategy="engineer",
                preferred_resource=res, id=eco2._new_id()
            )
            eco2.organisms.append(org)

    eco2.run(600)
    final2 = eco2.history[-1]

    # Считаем инженеров по ресурсам
    eng_by_res = Counter()
    for org in eco2.organisms:
        eng_by_res[org.preferred_resource] += 1
    total2 = len(eco2.organisms)
    print(f"  Популяция: {total2}")
    for res in resources:
        pct = eng_by_res[res] / total2 * 100 if total2 else 0
        print(f"    engineer-{res:>4}: {eng_by_res[res]:>5} ({pct:.1f}%)")

    final_terrain2 = Counter(eco2.terrain[y][x].value
                              for y in range(eco2.height) for x in range(eco2.width))
    print(f"  Финальный ландшафт: {dict(final_terrain2)}")

    # Подсчёт: какой terrain стал преобладать
    initial_terrain2 = Counter()
    eco_check = NicheEcosystem(width=35, height=35, seed=42)
    for y in range(35):
        for x in range(35):
            initial_terrain2[eco_check.terrain[y][x].value] += 1

    print(f"  Исходный ландшафт: {dict(initial_terrain2)}")
    print(f"  Изменение ландшафта:")
    for t in ["plain", "forest", "water", "mountain"]:
        diff = final_terrain2.get(t, 0) - initial_terrain2.get(t, 0)
        print(f"    {t:>10}: {diff:+d}")

    # Сохранение всех данных
    print("\n" + "=" * 70)
    print("ВЫВОДЫ")
    print("=" * 70)


if __name__ == "__main__":
    run_experiment()
