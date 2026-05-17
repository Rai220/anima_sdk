#!/usr/bin/env python3
"""
Эксперимент 7: Множественные давления — неустранимая сложность.

Предыдущий эксперимент (005) показал: эволюция минимизирует сложность.
SCAN один решает задачу "адаптация к изменениям". Один ген — достаточно.

Гипотеза: сложность становится неустранимой, когда среда предъявляет
НЕСКОЛЬКО ОДНОВРЕМЕННЫХ требований, каждое из которых требует своего гена.

Новые давления:
1. РЕСУРСЫ — нужно собирать (как раньше)
2. ХИЩНИКИ — появляются случайно, убивают если нет HIDE или FLEE
3. БОЛЕЗНИ — заражение от соседей, нужен IMMUNE
4. СЕЗОННОСТЬ — зимой нужен STORE, иначе голод
5. ТЕРРИТОРИАЛЬНОСТЬ — конкуренция за место, нужен DEFEND или MOVE

Каждое давление убивает, если нет ответа. Но каждый ответ стоит.
Минимальный геном должен покрыть ВСЕ давления одновременно.
"""

import random
import math
from collections import Counter
from evolvable import EvolvableEcosystem, EvolvableOrganism, GENES, GENE_COST

# Расширенный набор генов
EXTENDED_GENES = GENES + ["HIDE", "FLEE", "IMMUNE", "STORE", "DEFEND"]

EXTENDED_COST = {
    **GENE_COST,
    "HIDE": 0.15,      # Прятаться от хищников
    "FLEE": 0.2,       # Убегать от хищников (эффективнее, но дороже)
    "IMMUNE": 0.25,    # Устойчивость к болезням
    "STORE": 0.15,     # Запасы на зиму
    "DEFEND": 0.2,     # Защита территории
}


class MultiPressureEcosystem(EvolvableEcosystem):
    """Экосистема с множественными давлениями отбора."""

    def __init__(self, predator_rate=0.03, disease_rate=0.02,
                 winter_severity=0.5, territory_pressure=0.3,
                 **kwargs):
        super().__init__(**kwargs)
        self.predator_rate = predator_rate
        self.disease_rate = disease_rate
        self.winter_severity = winter_severity
        self.territory_pressure = territory_pressure
        # Болезни на карте
        self.disease_map = [[False] * self.width for _ in range(self.height)]

    def _apply_predation(self, org):
        """Хищники: случайные атаки. HIDE/FLEE спасают."""
        if self.rng.random() < self.predator_rate:
            if org.has("FLEE"):
                # Убегает — тратит энергию, но выживает
                org.energy -= 1.0
                nx, ny = self.rng.choice(self._neighbors(org.x, org.y))
                org.x, org.y = nx, ny
            elif org.has("HIDE"):
                # Прячется — меньше затрат, но пропускает ход сбора
                org.energy -= 0.3
                return True  # Сигнал: пропустить сбор
            else:
                # Атакован — большие потери
                org.energy -= 3.0
        return False

    def _apply_disease(self, org):
        """Болезни: заражение от соседей и среды. IMMUNE помогает."""
        # Заражение от карты
        if self.disease_map[org.y][org.x]:
            if org.has("IMMUNE"):
                pass  # Устойчив
            else:
                org.energy -= 1.5

        # Распространение болезней
        if self.rng.random() < self.disease_rate:
            self.disease_map[org.y][org.x] = True
        # Болезни со временем проходят
        if self.disease_map[org.y][org.x] and self.rng.random() < 0.1:
            self.disease_map[org.y][org.x] = False

    def _apply_winter(self, org):
        """Зима: без STORE теряешь энергию."""
        if self.season == 3:  # Зима
            if org.has("STORE"):
                pass  # Запасы спасают
            else:
                org.energy -= self.winter_severity

    def _apply_territory(self, org):
        """Территориальность: конкуренция за место."""
        neighbors_here = sum(1 for o in self.organisms
                            if o.id != org.id and o.x == org.x and o.y == org.y)
        if neighbors_here > 2:  # Перенаселение
            if org.has("DEFEND"):
                org.energy += 0.3  # Защитник получает бонус
            elif org.has("MOVE_BEST") or org.has("FLEE"):
                # Может уйти
                nx, ny = self.rng.choice(self._neighbors(org.x, org.y))
                org.x, org.y = nx, ny
            else:
                # Страдает от конкуренции
                org.energy -= self.territory_pressure * neighbors_here * 0.3

    def _act(self, org):
        """Действия с учётом множественных давлений."""
        # 1. Хищники (до сбора)
        skip_gather = self._apply_predation(org)

        # 2. Болезни
        self._apply_disease(org)

        # 3. Зима
        self._apply_winter(org)

        # 4. Территория
        self._apply_territory(org)

        if skip_gather:
            return  # Прятался — не собирает

        # 5. Сбор ресурсов (как в evolvable.py)
        cell = self.resources[org.y][org.x]

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

        if org.has("SPECIALIZE"):
            res = org.preferred_resource
            gathered = min(cell[res], 3.0) * 0.8
            cell[res] -= gathered
            org.energy += gathered
        elif org.has("SCAN"):
            best_res = max(cell, key=lambda r: cell[r])
            gathered = min(cell[best_res], 2.5) * 0.65
            cell[best_res] -= gathered
            org.energy += gathered
        elif org.has("GATHER"):
            best_res = max(cell, key=lambda r: cell[r])
            gathered = min(cell[best_res], 2.0) * 0.4
            cell[best_res] -= gathered
            org.energy += gathered

        if org.has("HOARD") and org.energy > 8.0:
            org.energy += 0.2

        if org.has("SHARE"):
            neighbors_here = [o for o in self.organisms
                             if o.id != org.id and o.x == org.x and o.y == org.y]
            for n in neighbors_here[:3]:
                if n.energy < 2.0 and org.energy > 5.0:
                    transfer = min(0.8, org.energy - 4.0)
                    org.energy -= transfer
                    n.energy += transfer * 0.7

    def step(self):
        self._produce_resources()
        self.rng.shuffle(self.organisms)

        for org in self.organisms:
            self._act(org)
            # Стоимость с расширенным набором генов
            cost = 0.5 + sum(EXTENDED_COST.get(g, 0.15) for g in org.genome)
            org.energy -= cost * self.cost_mult
            org.age += 1

        # Размножение
        new_organisms = []
        for org in self.organisms:
            if org.energy > 9.0 and self.rng.random() < 0.3:
                nx, ny = self.rng.choice(self._neighbors(org.x, org.y))
                child_genome = self._mutate_genome_extended(org.genome)
                child = EvolvableOrganism(
                    x=nx, y=ny,
                    energy=org.energy * 0.4,
                    genome=child_genome,
                    preferred_resource=org.preferred_resource,
                    id=self._new_id()
                )
                org.energy *= 0.5
                if self.rng.random() < 0.05:
                    child.preferred_resource = self.rng.choice(["food", "wood", "fish", "ore"])
                new_organisms.append(child)

        self.organisms.extend(new_organisms)
        self.organisms = [o for o in self.organisms if o.energy > 0]

        if len(self.organisms) > self.width * self.height * 2:
            self.organisms.sort(key=lambda o: o.energy)
            self.organisms = self.organisms[len(self.organisms) // 4:]

        self.step_num += 1
        self._record_extended()

    def _mutate_genome_extended(self, genome):
        new_genome = genome.copy()
        if self.rng.random() < self.mutation_rate:
            if new_genome:
                idx = self.rng.randint(0, len(new_genome) - 1)
                new_genome[idx] = self.rng.choice(EXTENDED_GENES)
        if self.rng.random() < self.mutation_rate * 0.5 and len(new_genome) < self.max_genome:
            new_genome.append(self.rng.choice(EXTENDED_GENES))
        if self.rng.random() < self.mutation_rate * 0.5 and len(new_genome) > 1:
            idx = self.rng.randint(0, len(new_genome) - 1)
            new_genome.pop(idx)
        return new_genome

    def _record_extended(self):
        total = len(self.organisms)
        if total == 0:
            self.history.append({"step": self.step_num, "total": 0,
                                "avg_complexity": 0, "gene_prevalence": {},
                                "top_genomes": [], "genome_length_dist": {}})
            return

        avg_complexity = sum(o.complexity for o in self.organisms) / total

        gene_counts = Counter()
        for o in self.organisms:
            for g in set(o.genome):
                gene_counts[g] += 1

        genome_strs = Counter("|".join(sorted(o.genome)) for o in self.organisms)
        top = genome_strs.most_common(5)

        len_dist = Counter(len(o.genome) for o in self.organisms)

        self.history.append({
            "step": self.step_num,
            "total": total,
            "avg_complexity": round(avg_complexity, 2),
            "gene_prevalence": {g: round(gene_counts.get(g, 0) / total * 100, 1)
                               for g in EXTENDED_GENES},
            "genome_length_dist": dict(len_dist),
            "top_genomes": [(g, c, round(c/total*100, 1)) for g, c in top],
        })


def run_experiment():
    print("=" * 70)
    print("МНОЖЕСТВЕННЫЕ ДАВЛЕНИЯ: НЕУСТРАНИМАЯ СЛОЖНОСТЬ?")
    print("=" * 70)

    # Эксперимент 1: Только ресурсы (контроль) vs все давления
    print("\n--- Контроль: только ресурсы ---")
    for seed in range(3):
        eco = MultiPressureEcosystem(
            predator_rate=0, disease_rate=0,
            winter_severity=0, territory_pressure=0,
            volatility=0.03, seed=seed
        )
        eco.seed_population(120)
        eco.run(800)
        f = eco.history[-1]
        print(f"  seed={seed}: pop={f['total']:>5} | len={f['avg_complexity']:.2f} | "
              f"top: {f['top_genomes'][0][0] if f['top_genomes'] else '?'}")

    print("\n--- Все давления ---")
    for seed in range(3):
        eco = MultiPressureEcosystem(
            predator_rate=0.03, disease_rate=0.02,
            winter_severity=0.5, territory_pressure=0.3,
            volatility=0.03, seed=seed
        )
        eco.seed_population(120)
        eco.run(800)
        f = eco.history[-1]
        if f['total'] > 0:
            print(f"  seed={seed}: pop={f['total']:>5} | len={f['avg_complexity']:.2f}")
            print(f"    genes: {f['gene_prevalence']}")
            print(f"    top: {f['top_genomes'][:3]}")
            print(f"    len_dist: {f['genome_length_dist']}")
        else:
            print(f"  seed={seed}: ВЫМЕРЛИ")

    # Эксперимент 2: Добавляем давления по одному
    print("\n--- Давления по одному (sweep, 6 seeds) ---")
    configs = [
        ("ресурсы",    dict(predator_rate=0,    disease_rate=0,    winter_severity=0,   territory_pressure=0)),
        ("+хищники",   dict(predator_rate=0.03, disease_rate=0,    winter_severity=0,   territory_pressure=0)),
        ("+болезни",   dict(predator_rate=0,    disease_rate=0.02, winter_severity=0,   territory_pressure=0)),
        ("+зима",      dict(predator_rate=0,    disease_rate=0,    winter_severity=0.5, territory_pressure=0)),
        ("+территория",dict(predator_rate=0,    disease_rate=0,    winter_severity=0,   territory_pressure=0.3)),
        ("хищ+бол",    dict(predator_rate=0.03, disease_rate=0.02, winter_severity=0,   territory_pressure=0)),
        ("хищ+зима",   dict(predator_rate=0.03, disease_rate=0,    winter_severity=0.5, territory_pressure=0)),
        ("все",        dict(predator_rate=0.03, disease_rate=0.02, winter_severity=0.5, territory_pressure=0.3)),
    ]

    print(f"{'config':>16} {'avg_len':>8} {'pop':>6} {'dominant_combo':>35}")
    for label, cfg in configs:
        lens = []
        pops = []
        top_genomes = Counter()
        for seed in range(6):
            eco = MultiPressureEcosystem(
                volatility=0.03, seed=seed, **cfg
            )
            eco.seed_population(120)
            eco.run(800)
            f = eco.history[-1]
            if f['total'] > 0:
                lens.append(f['avg_complexity'])
                pops.append(f['total'])
                if f['top_genomes']:
                    top_genomes[f['top_genomes'][0][0]] += 1

        if lens:
            avg_l = sum(lens) / len(lens)
            avg_p = sum(pops) / len(pops)
            top = top_genomes.most_common(1)[0][0] if top_genomes else "?"
            print(f"{label:>16} {avg_l:>8.2f} {avg_p:>6.0f} {top:>35}")
        else:
            print(f"{label:>16}  -- extinct --")

    # Эксперимент 3: Динамика сложности при всех давлениях
    print("\n--- Динамика: все давления, seed=0 ---")
    eco = MultiPressureEcosystem(
        predator_rate=0.03, disease_rate=0.02,
        winter_severity=0.5, territory_pressure=0.3,
        volatility=0.03, seed=0
    )
    eco.seed_population(150)
    eco.run(1000)

    for step in [0, 50, 100, 200, 400, 600, 800, 1000]:
        if step < len(eco.history):
            h = eco.history[step]
            if h['total'] > 0:
                genes = h.get('gene_prevalence', {})
                top_genes = sorted(genes.items(), key=lambda x: -x[1])[:4]
                top_str = ", ".join(f"{g}:{p:.0f}%" for g, p in top_genes)
                print(f"  step={step:>5}: pop={h['total']:>5} | len={h['avg_complexity']:.2f} | {top_str}")
            else:
                print(f"  step={step:>5}: EXTINCT")

    # Финальный анализ: какие комбинации генов возникли
    if eco.history[-1]['total'] > 0:
        print(f"\n--- Финальный состав ---")
        f = eco.history[-1]
        print(f"  Популяция: {f['total']}")
        print(f"  Средняя длина генома: {f['avg_complexity']:.2f}")
        print(f"  Распределение длин: {f['genome_length_dist']}")
        print(f"  Топ-5 геномов:")
        for genome, count, pct in f['top_genomes']:
            genes_list = genome.split("|")
            n_genes = len(genes_list)
            print(f"    [{n_genes} генов] {genome}: {count} ({pct}%)")
        print(f"\n  Распространённость генов:")
        for gene in sorted(f['gene_prevalence'].keys(),
                          key=lambda g: -f['gene_prevalence'][g]):
            pct = f['gene_prevalence'][gene]
            bar = "#" * int(pct / 2)
            print(f"    {gene:>12}: {pct:>5.1f}% {bar}")


if __name__ == "__main__":
    run_experiment()
