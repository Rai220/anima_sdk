#!/usr/bin/env python3
"""
Эксперимент 6: Эволюция сложности.

Во всех предыдущих экспериментах стратегии были фиксированы:
gatherer, specialist, adaptive, nomad, symbiont, engineer.

Здесь стратегия — это геном: набор правил (генов), которые мутируют
и рекомбинируются при размножении. Сложность не задана — она *возникает*.

Геном — список генов, каждый ген = одно правило поведения:
  - GATHER: собирай лучший ресурс (эфф. 0.4)
  - SPECIALIZE: собирай только preferred_resource (эфф. 0.8)
  - SCAN: выбери лучший ресурс в текущей клетке (эфф. 0.65)
  - MOVE_BEST: перейди на клетку с наибольшим ресурсом из соседних
  - SHARE: поделись энергией с соседом, у которого мало
  - HOARD: не делись, но получай бонус за запасы
  - MEMORY: запомни текущую клетку, потом возвращайся к лучшей

Каждый ген стоит дополнительные затраты на поддержание.
Больше генов = больше возможностей, но выше расходы.

Вопрос: какой длины геном *оптимален* при разных уровнях волатильности?
Возникнут ли сложные комбинации генов, не заложенные в дизайн?
"""

import random
import math
import json
from collections import Counter
from ecosystem import Ecosystem, Terrain, Organism, TERRAIN_YIELD


GENES = ["GATHER", "SPECIALIZE", "SCAN", "MOVE_BEST", "SHARE", "HOARD", "MEMORY"]

# Затраты за каждый ген в геноме
GENE_COST = {
    "GATHER": 0.1,
    "SPECIALIZE": 0.15,
    "SCAN": 0.2,
    "MOVE_BEST": 0.25,
    "SHARE": 0.15,
    "HOARD": 0.1,
    "MEMORY": 0.2,
}


class EvolvableOrganism:
    """Организм с эволюционирующим геномом."""
    __slots__ = ['x', 'y', 'energy', 'genome', 'preferred_resource',
                 'memory_spots', 'age', 'id']

    def __init__(self, x, y, energy, genome, preferred_resource="food", id=0):
        self.x = x
        self.y = y
        self.energy = energy
        self.genome = genome  # list of gene strings
        self.preferred_resource = preferred_resource
        self.memory_spots = []  # (x, y, value)
        self.age = 0
        self.id = id

    @property
    def maintenance_cost(self):
        base = 0.5
        return base + sum(GENE_COST[g] for g in self.genome)

    @property
    def complexity(self):
        return len(self.genome)

    @property
    def unique_genes(self):
        return len(set(self.genome))

    def has(self, gene):
        return gene in self.genome


class EvolvableEcosystem:
    """Экосистема с эволюционирующими организмами."""

    def __init__(self, width=35, height=35, seed=42,
                 volatility=0.0, resource_mult=1.3, cost_mult=0.7,
                 mutation_rate=0.1, max_genome=8):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.step_num = 0
        self.next_id = 0
        self.volatility = volatility
        self.resource_mult = resource_mult
        self.cost_mult = cost_mult
        self.mutation_rate = mutation_rate
        self.max_genome = max_genome
        self.organisms: list[EvolvableOrganism] = []
        self.history = []

        # Terrain generation (same as Ecosystem)
        self.terrain = self._generate_terrain()
        self.resources = [[{r: 0.0 for r in ["food", "wood", "fish", "ore"]}
                           for _ in range(width)] for _ in range(height)]

    def _generate_terrain(self):
        terrains = list(Terrain)
        seeds = []
        for t in terrains:
            for _ in range(self.rng.randint(3, 6)):
                seeds.append((self.rng.randint(0, self.width-1),
                              self.rng.randint(0, self.height-1), t))
        grid = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
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

    def _new_id(self):
        self.next_id += 1
        return self.next_id

    @property
    def season(self):
        return (self.step_num // 25) % 4

    def _neighbors(self, x, y):
        result = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                result.append(((x + dx) % self.width, (y + dy) % self.height))
        return result

    def seed_population(self, n=100):
        """Засеивает популяцию с разными начальными геномами."""
        resources = ["food", "wood", "fish", "ore"]
        # Начальные геномы: от 1 до 4 случайных генов
        for _ in range(n):
            genome_len = self.rng.randint(1, 4)
            genome = [self.rng.choice(GENES) for _ in range(genome_len)]
            x = self.rng.randint(0, self.width - 1)
            y = self.rng.randint(0, self.height - 1)
            org = EvolvableOrganism(
                x=x, y=y, energy=8.0,
                genome=genome,
                preferred_resource=self.rng.choice(resources),
                id=self._new_id()
            )
            self.organisms.append(org)

    def _produce_resources(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.rng.random() < self.volatility:
                    self.terrain[y][x] = self.rng.choice(list(Terrain))
                    self.resources[y][x] = {r: 0.0 for r in ["food", "wood", "fish", "ore"]}

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

    def _act(self, org: EvolvableOrganism):
        """Выполняет действия организма согласно его геному."""
        cell = self.resources[org.y][org.x]
        gathered = 0.0

        # MOVE_BEST: перемещение к лучшей клетке (до сбора)
        if org.has("MOVE_BEST"):
            total_here = sum(cell.values())
            best_pos = (org.x, org.y)
            best_total = total_here
            for nx, ny in self._neighbors(org.x, org.y):
                t = sum(self.resources[ny][nx].values())
                if t > best_total:
                    best_total = t
                    best_pos = (nx, ny)
            if best_pos != (org.x, org.y):
                org.x, org.y = best_pos
                org.energy -= 0.2
                cell = self.resources[org.y][org.x]

        # MEMORY: возвращение к лучшему запомненному месту
        if org.has("MEMORY"):
            total_here = sum(cell.values())
            org.memory_spots.append((org.x, org.y, total_here))
            if len(org.memory_spots) > 10:
                org.memory_spots.pop(0)
            if total_here < 1.5 and org.memory_spots:
                best_spot = max(org.memory_spots, key=lambda s: s[2])
                if best_spot[2] > total_here * 1.5:
                    org.x, org.y = best_spot[0], best_spot[1]
                    org.energy -= 0.3
                    cell = self.resources[org.y][org.x]

        # Сбор ресурсов (приоритет: SPECIALIZE > SCAN > GATHER)
        if org.has("SPECIALIZE"):
            res = org.preferred_resource
            gathered = min(cell[res], 3.0) * 0.8
            cell[res] -= gathered
        elif org.has("SCAN"):
            best_res = max(cell, key=lambda r: cell[r])
            gathered = min(cell[best_res], 2.5) * 0.65
            cell[best_res] -= gathered
        elif org.has("GATHER"):
            best_res = max(cell, key=lambda r: cell[r])
            gathered = min(cell[best_res], 2.0) * 0.4
            cell[best_res] -= gathered

        org.energy += gathered

        # HOARD: бонус за большие запасы энергии
        if org.has("HOARD") and org.energy > 8.0:
            org.energy += 0.2  # Маленький бонус — проценты на капитал

        # SHARE: поделиться с соседями на той же клетке
        if org.has("SHARE"):
            neighbors_here = [o for o in self.organisms
                             if o.id != org.id and o.x == org.x and o.y == org.y]
            for n in neighbors_here[:3]:  # Максимум 3 соседа
                if n.energy < 2.0 and org.energy > 5.0:
                    transfer = min(0.8, org.energy - 4.0)
                    org.energy -= transfer
                    n.energy += transfer * 0.7

    def _mutate_genome(self, genome):
        """Мутация генома при размножении."""
        new_genome = genome.copy()

        # Точечная мутация: замена гена
        if self.rng.random() < self.mutation_rate:
            if new_genome:
                idx = self.rng.randint(0, len(new_genome) - 1)
                new_genome[idx] = self.rng.choice(GENES)

        # Дупликация: добавление гена
        if self.rng.random() < self.mutation_rate * 0.5 and len(new_genome) < self.max_genome:
            new_genome.append(self.rng.choice(GENES))

        # Делеция: удаление гена
        if self.rng.random() < self.mutation_rate * 0.5 and len(new_genome) > 1:
            idx = self.rng.randint(0, len(new_genome) - 1)
            new_genome.pop(idx)

        return new_genome

    def step(self):
        self._produce_resources()
        self.rng.shuffle(self.organisms)

        for org in self.organisms:
            self._act(org)
            org.energy -= org.maintenance_cost * self.cost_mult
            org.age += 1

        # Размножение
        new_organisms = []
        for org in self.organisms:
            if org.energy > 9.0 and self.rng.random() < 0.3:
                nx, ny = self.rng.choice(self._neighbors(org.x, org.y))
                child_genome = self._mutate_genome(org.genome)
                child = EvolvableOrganism(
                    x=nx, y=ny,
                    energy=org.energy * 0.4,
                    genome=child_genome,
                    preferred_resource=org.preferred_resource,
                    id=self._new_id()
                )
                org.energy *= 0.5
                # Мутация preferred_resource
                if self.rng.random() < 0.05:
                    child.preferred_resource = self.rng.choice(["food", "wood", "fish", "ore"])
                new_organisms.append(child)

        self.organisms.extend(new_organisms)
        self.organisms = [o for o in self.organisms if o.energy > 0]

        if len(self.organisms) > self.width * self.height * 2:
            self.organisms.sort(key=lambda o: o.energy)
            self.organisms = self.organisms[len(self.organisms) // 4:]

        self.step_num += 1
        self._record()

    def _record(self):
        total = len(self.organisms)
        if total == 0:
            self.history.append({"step": self.step_num, "total": 0,
                                "avg_complexity": 0, "avg_unique": 0,
                                "shannon_genes": 0, "genome_dist": {},
                                "top_genomes": []})
            return

        avg_complexity = sum(o.complexity for o in self.organisms) / total
        avg_unique = sum(o.unique_genes for o in self.organisms) / total

        # Распределение генов
        gene_counts = Counter()
        for o in self.organisms:
            for g in set(o.genome):  # Уникальные гены в каждом организме
                gene_counts[g] += 1

        # Shannon по генам
        shannon = 0.0
        total_gene_presence = sum(gene_counts.values())
        for c in gene_counts.values():
            p = c / total_gene_presence
            if p > 0:
                shannon -= p * math.log2(p)

        # Топ-5 геномов
        genome_strs = Counter("|".join(sorted(o.genome)) for o in self.organisms)
        top = genome_strs.most_common(5)

        # Распределение по длине генома
        len_dist = Counter(len(o.genome) for o in self.organisms)

        self.history.append({
            "step": self.step_num,
            "total": total,
            "avg_complexity": round(avg_complexity, 2),
            "avg_unique": round(avg_unique, 2),
            "shannon_genes": round(shannon, 3),
            "gene_prevalence": {g: round(gene_counts.get(g, 0) / total * 100, 1) for g in GENES},
            "genome_length_dist": dict(len_dist),
            "top_genomes": [(g, c, round(c/total*100, 1)) for g, c in top],
        })

    def run(self, steps=600):
        self._record()
        for _ in range(steps):
            self.step()
        return self.history


def run_experiment():
    print("=" * 70)
    print("ЭВОЛЮЦИЯ СЛОЖНОСТИ: ГЕНОМЫ, МУТАЦИИ, ОТБОР")
    print("=" * 70)

    # Эксперимент 1: Стабильная среда — какие геномы выживают?
    print("\n--- Стабильная среда (v=0.0) ---")
    for seed in range(3):
        eco = EvolvableEcosystem(volatility=0.0, seed=seed)
        eco.seed_population(120)
        eco.run(800)
        final = eco.history[-1]
        print(f"  seed={seed}: pop={final['total']:>5} | avg_len={final['avg_complexity']:.2f} | "
              f"avg_unique={final['avg_unique']:.2f}")
        print(f"    genes: {final['gene_prevalence']}")
        print(f"    top genomes: {final['top_genomes'][:3]}")
        print(f"    len dist: {final['genome_length_dist']}")

    # Эксперимент 2: Волатильная среда
    print("\n--- Волатильная среда (v=0.03) ---")
    for seed in range(3):
        eco = EvolvableEcosystem(volatility=0.03, seed=seed)
        eco.seed_population(120)
        eco.run(800)
        final = eco.history[-1]
        print(f"  seed={seed}: pop={final['total']:>5} | avg_len={final['avg_complexity']:.2f} | "
              f"avg_unique={final['avg_unique']:.2f}")
        print(f"    genes: {final['gene_prevalence']}")
        print(f"    top genomes: {final['top_genomes'][:3]}")
        print(f"    len dist: {final['genome_length_dist']}")

    # Эксперимент 3: Sweep по волатильности — как средняя сложность зависит
    print("\n--- Sweep по волатильности (8 seeds) ---")
    print(f"{'vol':>6} {'avg_len':>8} {'avg_uniq':>9} {'pop':>6} {'top_genome':>30}")
    for v in [0.0, 0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.1]:
        lens = []
        uniqs = []
        pops = []
        top_genomes = Counter()
        for seed in range(8):
            eco = EvolvableEcosystem(volatility=v, seed=seed)
            eco.seed_population(100)
            eco.run(700)
            final = eco.history[-1]
            if final['total'] > 0:
                lens.append(final['avg_complexity'])
                uniqs.append(final['avg_unique'])
                pops.append(final['total'])
                if final['top_genomes']:
                    top_genomes[final['top_genomes'][0][0]] += 1

        if lens:
            avg_l = sum(lens) / len(lens)
            avg_u = sum(uniqs) / len(uniqs)
            avg_p = sum(pops) / len(pops)
            most_common = top_genomes.most_common(1)[0][0] if top_genomes else "?"
            print(f"{v:>6.3f} {avg_l:>8.2f} {avg_u:>9.2f} {avg_p:>6.0f} {most_common:>30}")
        else:
            print(f"{v:>6.3f}  -- extinct --")

    # Эксперимент 4: Динамика эволюции — как меняется сложность со временем
    print("\n--- Динамика: сложность по шагам (v=0.03, seed=0) ---")
    eco = EvolvableEcosystem(volatility=0.03, seed=0)
    eco.seed_population(120)
    eco.run(1000)

    checkpoints = [0, 50, 100, 200, 400, 600, 800, 1000]
    for step in checkpoints:
        if step < len(eco.history):
            h = eco.history[step]
            genes = h.get('gene_prevalence', {})
            top_genes = sorted(genes.items(), key=lambda x: -x[1])[:3]
            top_str = ", ".join(f"{g}:{p:.0f}%" for g, p in top_genes)
            print(f"  step={step:>5}: pop={h['total']:>5} | len={h['avg_complexity']:.2f} | "
                  f"genes: {top_str}")


if __name__ == "__main__":
    run_experiment()
