#!/usr/bin/env python3
"""
Коэволюция как источник сложности.

Gen 9 показал: эволюция — оптимизатор, не генератор сложности.
Геномы сокращаются до минимума, потому что давление было *внешним* (случайная волатильность).

Гипотеза: если давление *эндогенное* (другие эволюционирующие организмы),
сложность не схлопывается, а растёт — гонка вооружений (Red Queen).

Модель: хищники и жертвы на 2D решётке.
- Жертвы: собирают ресурсы, защищаются
- Хищники: охотятся на жертв
- Оба вида имеют эволюционируемые геномы
- Сложность генома = число генов (каждый ген стоит энергию)

Гены жертв:
  GATHER    — базовый сбор ресурсов (эфф. 0.4)
  SCAN      — выбрать лучший ресурс (эфф. 0.65)
  HIDE      — снижение вероятности быть пойманным (0.3 → ×0.5)
  FLOCK     — бонус к выживанию рядом с сородичами
  DETECT    — обнаружить хищника и убежать
  HOARD     — бонус за большие запасы

Гены хищников:
  HUNT      — базовая охота (вероятность поймать 0.3)
  STALK     — повышенная вероятность (+0.15)
  PACK      — бонус при наличии других хищников рядом
  SPEED     — возможность двигаться к ближайшей жертве
  AMBUSH    — усиление против DETECT (нейтрализует)
  ENDURE    — меньше затрат энергии при голоде
"""

import random
import math
from collections import Counter


PREY_GENES = ["GATHER", "SCAN", "HIDE", "FLOCK", "DETECT", "HOARD"]
PRED_GENES = ["HUNT", "STALK", "PACK", "SPEED", "AMBUSH", "ENDURE"]

PREY_GENE_COST = {
    "GATHER": 0.08, "SCAN": 0.15, "HIDE": 0.12,
    "FLOCK": 0.10, "DETECT": 0.18, "HOARD": 0.08,
}
PRED_GENE_COST = {
    "HUNT": 0.10, "STALK": 0.15, "PACK": 0.12,
    "SPEED": 0.20, "AMBUSH": 0.15, "ENDURE": 0.08,
}


class Organism:
    __slots__ = ['x', 'y', 'energy', 'genome', 'role', 'age', 'id']

    def __init__(self, x, y, energy, genome, role, id=0):
        self.x = x
        self.y = y
        self.energy = energy
        self.genome = genome  # list of gene strings
        self.role = role      # "prey" or "predator"
        self.age = 0
        self.id = id

    def has(self, gene):
        return gene in self.genome

    @property
    def maintenance_cost(self):
        costs = PREY_GENE_COST if self.role == "prey" else PRED_GENE_COST
        base = 0.4 if self.role == "prey" else 0.6
        return base + sum(costs.get(g, 0.1) for g in self.genome)

    @property
    def complexity(self):
        return len(self.genome)

    @property
    def unique_genes(self):
        return len(set(self.genome))


class CoevolutionaryEcosystem:
    def __init__(self, width=30, height=30, seed=42,
                 mutation_rate=0.12, max_genome=8):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.step_num = 0
        self.next_id = 0
        self.mutation_rate = mutation_rate
        self.max_genome = max_genome
        self.organisms: list[Organism] = []
        self.history = []

        # Ресурсы на каждой клетке (для жертв)
        self.resources = [[0.0] * width for _ in range(height)]

    def _new_id(self):
        self.next_id += 1
        return self.next_id

    def _neighbors(self, x, y):
        result = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                result.append(((x + dx) % self.width, (y + dy) % self.height))
        return result

    def seed_population(self, n_prey=120, n_pred=30):
        """Засеивает популяции с разными начальными геномами."""
        for _ in range(n_prey):
            genome_len = self.rng.randint(1, 3)
            genome = [self.rng.choice(PREY_GENES) for _ in range(genome_len)]
            x = self.rng.randint(0, self.width - 1)
            y = self.rng.randint(0, self.height - 1)
            self.organisms.append(Organism(
                x=x, y=y, energy=6.0, genome=genome,
                role="prey", id=self._new_id()
            ))

        for _ in range(n_pred):
            genome_len = self.rng.randint(1, 3)
            genome = [self.rng.choice(PRED_GENES) for _ in range(genome_len)]
            x = self.rng.randint(0, self.width - 1)
            y = self.rng.randint(0, self.height - 1)
            self.organisms.append(Organism(
                x=x, y=y, energy=8.0, genome=genome,
                role="predator", id=self._new_id()
            ))

    def _produce_resources(self):
        """Ресурсы восстанавливаются каждый шаг."""
        for y in range(self.height):
            for x in range(self.width):
                self.resources[y][x] = min(
                    self.resources[y][x] + 1.2 + self.rng.random() * 0.6,
                    10.0
                )

    def _act_prey(self, org):
        """Жертва: собирает ресурсы."""
        cell_val = self.resources[org.y][org.x]

        if org.has("SCAN"):
            gathered = min(cell_val, 2.5) * 0.65
        elif org.has("GATHER"):
            gathered = min(cell_val, 2.0) * 0.4
        else:
            gathered = min(cell_val, 1.5) * 0.3  # Без гена сбора — минимум

        self.resources[org.y][org.x] -= gathered
        org.energy += gathered

        # HOARD: бонус за большие запасы
        if org.has("HOARD") and org.energy > 6.0:
            org.energy += 0.15

    def _act_predator(self, org):
        """Хищник: охотится на жертв."""
        # SPEED: двигаться к ближайшей жертве
        if org.has("SPEED"):
            prey_here = [o for o in self.organisms
                        if o.role == "prey" and o.x == org.x and o.y == org.y]
            if not prey_here:
                # Ищем жертву в соседних клетках
                for nx, ny in self._neighbors(org.x, org.y):
                    prey_near = [o for o in self.organisms
                                if o.role == "prey" and o.x == nx and o.y == ny]
                    if prey_near:
                        org.x, org.y = nx, ny
                        org.energy -= 0.15
                        break

        # Поиск жертвы на своей клетке
        prey_here = [o for o in self.organisms
                    if o.role == "prey" and o.x == org.x and o.y == org.y
                    and o.energy > 0]

        if not prey_here:
            # Голодный хищник
            if org.has("ENDURE"):
                org.energy -= 0.1  # Меньше потерь от голода
            return

        target = self.rng.choice(prey_here)

        # Вероятность поимки
        catch_prob = 0.25
        if org.has("HUNT"):
            catch_prob = 0.35
        if org.has("STALK"):
            catch_prob += 0.15

        # PACK: бонус от других хищников рядом
        if org.has("PACK"):
            pred_here = sum(1 for o in self.organisms
                          if o.role == "predator" and o.x == org.x and o.y == org.y
                          and o.id != org.id)
            catch_prob += min(pred_here * 0.08, 0.2)

        # Защита жертвы
        # DETECT: жертва обнаруживает хищника и убегает
        if target.has("DETECT") and not org.has("AMBUSH"):
            if self.rng.random() < 0.4:
                # Жертва убежала
                nx, ny = self.rng.choice(self._neighbors(target.x, target.y))
                target.x, target.y = nx, ny
                target.energy -= 0.2
                return

        # HIDE: жертва труднее обнаруживается
        if target.has("HIDE"):
            catch_prob *= 0.5

        # FLOCK: защита в стае
        if target.has("FLOCK"):
            flock_size = sum(1 for o in self.organisms
                           if o.role == "prey" and o.x == target.x and o.y == target.y
                           and o.id != target.id)
            if flock_size >= 2:
                catch_prob *= 0.6  # Стая снижает вероятность

        # Попытка поймать
        if self.rng.random() < catch_prob:
            energy_gain = min(target.energy * 0.7, 5.0)
            org.energy += energy_gain
            target.energy = 0  # Жертва погибает

    def _mutate_genome(self, genome, role):
        """Мутация генома при размножении."""
        genes = PREY_GENES if role == "prey" else PRED_GENES
        new_genome = genome.copy()

        # Точечная мутация
        if self.rng.random() < self.mutation_rate:
            if new_genome:
                idx = self.rng.randint(0, len(new_genome) - 1)
                new_genome[idx] = self.rng.choice(genes)

        # Дупликация
        if self.rng.random() < self.mutation_rate * 0.5 and len(new_genome) < self.max_genome:
            new_genome.append(self.rng.choice(genes))

        # Делеция
        if self.rng.random() < self.mutation_rate * 0.5 and len(new_genome) > 1:
            idx = self.rng.randint(0, len(new_genome) - 1)
            new_genome.pop(idx)

        return new_genome

    def step(self):
        self._produce_resources()
        self.rng.shuffle(self.organisms)

        # Сначала жертвы собирают ресурсы
        for org in self.organisms:
            if org.role == "prey" and org.energy > 0:
                self._act_prey(org)

        # Затем хищники охотятся
        for org in self.organisms:
            if org.role == "predator" and org.energy > 0:
                self._act_predator(org)

        # Затраты на поддержание
        for org in self.organisms:
            org.energy -= org.maintenance_cost * 0.7
            org.age += 1

        # Размножение
        new_organisms = []
        for org in self.organisms:
            threshold = 8.0 if org.role == "prey" else 10.0
            if org.energy > threshold and self.rng.random() < 0.25:
                nx, ny = self.rng.choice(self._neighbors(org.x, org.y))
                child_genome = self._mutate_genome(org.genome, org.role)
                child = Organism(
                    x=nx, y=ny,
                    energy=org.energy * 0.35,
                    genome=child_genome,
                    role=org.role,
                    id=self._new_id()
                )
                org.energy *= 0.55
                new_organisms.append(child)

        self.organisms.extend(new_organisms)
        self.organisms = [o for o in self.organisms if o.energy > 0]

        # Carrying capacity
        max_pop = self.width * self.height * 3
        if len(self.organisms) > max_pop:
            self.organisms.sort(key=lambda o: o.energy)
            self.organisms = self.organisms[len(self.organisms) // 3:]

        self.step_num += 1
        self._record()

    def _record(self):
        prey = [o for o in self.organisms if o.role == "prey"]
        pred = [o for o in self.organisms if o.role == "predator"]

        def genome_stats(organisms, gene_list):
            if not organisms:
                return {"count": 0, "avg_complexity": 0, "avg_unique": 0,
                        "gene_prevalence": {}, "top_genomes": [],
                        "genome_length_dist": {}}
            n = len(organisms)
            avg_c = sum(o.complexity for o in organisms) / n
            avg_u = sum(o.unique_genes for o in organisms) / n

            gene_counts = Counter()
            for o in organisms:
                for g in set(o.genome):
                    gene_counts[g] += 1
            prevalence = {g: round(gene_counts.get(g, 0) / n * 100, 1) for g in gene_list}

            genome_strs = Counter("|".join(sorted(o.genome)) for o in organisms)
            top = genome_strs.most_common(5)
            top_genomes = [(g, c, round(c / n * 100, 1)) for g, c in top]

            len_dist = Counter(len(o.genome) for o in organisms)

            return {
                "count": n,
                "avg_complexity": round(avg_c, 2),
                "avg_unique": round(avg_u, 2),
                "gene_prevalence": prevalence,
                "top_genomes": top_genomes,
                "genome_length_dist": dict(len_dist),
            }

        self.history.append({
            "step": self.step_num,
            "prey": genome_stats(prey, PREY_GENES),
            "predator": genome_stats(pred, PRED_GENES),
        })

    def run(self, steps=600):
        self._record()
        for _ in range(steps):
            self.step()
            # Если одна из популяций вымерла
            prey_alive = any(o.role == "prey" for o in self.organisms)
            pred_alive = any(o.role == "predator" for o in self.organisms)
            if not prey_alive or not pred_alive:
                break
        return self.history


def print_snapshot(label, h):
    """Печатает снимок состояния."""
    prey = h["prey"]
    pred = h["predator"]
    print(f"  {label}: prey={prey['count']:>4} (len={prey['avg_complexity']:.2f}) | "
          f"pred={pred['count']:>4} (len={pred['avg_complexity']:.2f})")
    if prey["top_genomes"]:
        top_prey = prey["top_genomes"][0]
        print(f"    prey top: {top_prey[0]} ({top_prey[2]}%)")
    if pred["top_genomes"]:
        top_pred = pred["top_genomes"][0]
        print(f"    pred top: {top_pred[0]} ({top_pred[2]}%)")


def run_experiment():
    print("=" * 70)
    print("КОЭВОЛЮЦИЯ: ГЕНЕРИРУЕТ ЛИ ГОНКА ВООРУЖЕНИЙ СЛОЖНОСТЬ?")
    print("=" * 70)

    # Эксперимент 1: Базовый запуск — динамика сложности
    print("\n--- Эксперимент 1: Динамика коэволюции (3 seed) ---")
    for seed in range(3):
        print(f"\n  seed={seed}:")
        eco = CoevolutionaryEcosystem(seed=seed)
        eco.seed_population(120, 30)
        eco.run(1000)

        checkpoints = [0, 100, 200, 400, 600, 800, 1000]
        for step in checkpoints:
            if step < len(eco.history):
                print_snapshot(f"step={step:>4}", eco.history[step])

        # Итог: сравниваем начальную и конечную сложность
        h0 = eco.history[0]
        hf = eco.history[-1]
        print(f"  ИТОГ: prey len {h0['prey']['avg_complexity']:.2f} → {hf['prey']['avg_complexity']:.2f} | "
              f"pred len {h0['predator']['avg_complexity']:.2f} → {hf['predator']['avg_complexity']:.2f}")

    # Эксперимент 2: Сравнение — с хищниками vs без хищников
    print("\n\n--- Эксперимент 2: С хищниками vs без (контроль) ---")
    print("  (Контроль: жертвы без хищников = чистая среда из gen9)")

    coevo_lens = []
    control_lens = []

    for seed in range(8):
        # С хищниками
        eco = CoevolutionaryEcosystem(seed=seed)
        eco.seed_population(120, 30)
        eco.run(800)
        hf = eco.history[-1]
        if hf["prey"]["count"] > 0:
            coevo_lens.append(hf["prey"]["avg_complexity"])

        # Без хищников (контроль)
        eco_ctrl = CoevolutionaryEcosystem(seed=seed)
        eco_ctrl.seed_population(120, 0)  # 0 хищников
        eco_ctrl.run(800)
        hf_ctrl = eco_ctrl.history[-1]
        if hf_ctrl["prey"]["count"] > 0:
            control_lens.append(hf_ctrl["prey"]["avg_complexity"])

    if coevo_lens and control_lens:
        avg_coevo = sum(coevo_lens) / len(coevo_lens)
        avg_ctrl = sum(control_lens) / len(control_lens)
        print(f"  С хищниками:  avg prey genome len = {avg_coevo:.2f} (n={len(coevo_lens)})")
        print(f"  Без хищников: avg prey genome len = {avg_ctrl:.2f} (n={len(control_lens)})")
        diff = avg_coevo - avg_ctrl
        print(f"  Разница: {diff:+.2f}")
        if diff > 0.15:
            print("  → Коэволюция УВЕЛИЧИВАЕТ сложность жертв")
        elif diff < -0.15:
            print("  → Коэволюция УМЕНЬШАЕТ сложность жертв (давление на эффективность)")
        else:
            print("  → Разница незначительна")

    # Эксперимент 3: Гонка вооружений — как гены атаки/защиты коррелируют
    print("\n\n--- Эксперимент 3: Гонка вооружений (корреляция атака/защита) ---")
    eco = CoevolutionaryEcosystem(seed=42)
    eco.seed_population(150, 40)
    eco.run(1200)

    print(f"  {'step':>5} | {'prey HIDE':>9} {'prey DETECT':>11} {'prey FLOCK':>10} | "
          f"{'pred STALK':>10} {'pred AMBUSH':>11} {'pred PACK':>9}")
    print("  " + "-" * 80)

    for step in [0, 100, 200, 400, 600, 800, 1000, 1200]:
        if step < len(eco.history):
            h = eco.history[step]
            pp = h["prey"]["gene_prevalence"]
            pr = h["predator"]["gene_prevalence"]
            if pp and pr:
                print(f"  {step:>5} | {pp.get('HIDE', 0):>8.1f}% {pp.get('DETECT', 0):>10.1f}% "
                      f"{pp.get('FLOCK', 0):>9.1f}% | "
                      f"{pr.get('STALK', 0):>9.1f}% {pr.get('AMBUSH', 0):>10.1f}% "
                      f"{pr.get('PACK', 0):>8.1f}%")

    # Финальный анализ
    print("\n\n" + "=" * 70)
    print("АНАЛИЗ")
    print("=" * 70)

    hf = eco.history[-1]
    prey_genes = hf["prey"]["gene_prevalence"]
    pred_genes = hf["predator"]["gene_prevalence"]

    print(f"\nЖертвы (n={hf['prey']['count']}):")
    print(f"  Средняя длина генома: {hf['prey']['avg_complexity']:.2f}")
    print(f"  Гены: {prey_genes}")
    print(f"  Топ-3 генома: {hf['prey']['top_genomes'][:3]}")

    print(f"\nХищники (n={hf['predator']['count']}):")
    print(f"  Средняя длина генома: {hf['predator']['avg_complexity']:.2f}")
    print(f"  Гены: {pred_genes}")
    print(f"  Топ-3 генома: {hf['predator']['top_genomes'][:3]}")


if __name__ == "__main__":
    run_experiment()
