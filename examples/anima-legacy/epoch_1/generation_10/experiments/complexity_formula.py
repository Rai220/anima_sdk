#!/usr/bin/env python3
"""
Проверка формулы: сложность = стоимость_ошибки × разнообразие_давлений.

Используем хищник-жертву (coevolution.py) как стабильную базу.
Варьируем два параметра:
1. error_cost: штраф хищника за промах (базовый расход энергии)
   - low: хищник может долго голодать (0.3)
   - medium: стандарт (0.6)
   - high: хищник быстро умирает без добычи (0.9)

2. pressure_diversity: количество доступных генов
   - low: 2 гена атаки, 2 защиты
   - medium: 4 гена атаки, 4 защиты
   - high: 6 генов атаки, 6 защиты

Если формула верна:
- Сложность(high, high) >> Сложность(low, low)
- Эффект мультипликативный, не аддитивный
"""

import random
import math
from collections import Counter


def make_gene_sets(n_types):
    """Создаёт наборы генов для жертв и хищников."""
    prey_gather = ["GATHER", "SCAN"]
    pred_base = ["HUNT", "SPEED"]

    # Добавляем пары атака/защита
    prey_defense = [f"HIDE_{i}" for i in range(n_types)]
    pred_attack = [f"COUNTER_{i}" for i in range(n_types)]

    return prey_gather + prey_defense, pred_base + pred_attack


class Organism:
    __slots__ = ['x', 'y', 'energy', 'genome', 'role', 'age', 'id']

    def __init__(self, x, y, energy, genome, role, id=0):
        self.x = x
        self.y = y
        self.energy = energy
        self.genome = genome
        self.role = role
        self.age = 0
        self.id = id

    def has(self, gene):
        return gene in self.genome

    @property
    def complexity(self):
        return len(self.genome)

    @property
    def unique_genes(self):
        return len(set(self.genome))


class ParameterizedEcosystem:
    """Экосистема с настраиваемыми error_cost и pressure_diversity."""

    def __init__(self, n_defense_types=4, pred_base_cost=0.6,
                 width=25, height=25, seed=42,
                 mutation_rate=0.12, max_genome=10):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.step_num = 0
        self.next_id = 0
        self.mutation_rate = mutation_rate
        self.max_genome = max_genome
        self.n_defense_types = n_defense_types
        self.pred_base_cost = pred_base_cost  # Стоимость ошибки хищника
        self.organisms: list[Organism] = []
        self.history = []
        self.resources = [[0.0] * width for _ in range(height)]

        # Генерируем наборы генов
        self.prey_genes, self.pred_genes = make_gene_sets(n_defense_types)

        # Стоимость за ген
        self.gene_cost = 0.12

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

    def seed_population(self, n_prey=100, n_pred=25):
        for _ in range(n_prey):
            n = self.rng.randint(1, 3)
            genome = [self.rng.choice(self.prey_genes) for _ in range(n)]
            x = self.rng.randint(0, self.width - 1)
            y = self.rng.randint(0, self.height - 1)
            self.organisms.append(Organism(
                x=x, y=y, energy=6.0, genome=genome,
                role="prey", id=self._new_id()
            ))
        for _ in range(n_pred):
            n = self.rng.randint(1, 3)
            genome = [self.rng.choice(self.pred_genes) for _ in range(n)]
            x = self.rng.randint(0, self.width - 1)
            y = self.rng.randint(0, self.height - 1)
            self.organisms.append(Organism(
                x=x, y=y, energy=8.0, genome=genome,
                role="predator", id=self._new_id()
            ))

    def _produce_resources(self):
        for y in range(self.height):
            for x in range(self.width):
                self.resources[y][x] = min(
                    self.resources[y][x] + 1.2 + self.rng.random() * 0.5, 10.0
                )

    def _catch_probability(self, pred, prey):
        """Вероятность поимки с учётом генов атаки/защиты."""
        base = 0.15
        if pred.has("HUNT"):
            base = 0.30
        if pred.has("SPEED"):
            base += 0.10

        # Каждый HIDE_i снижает вероятность, если у хищника нет COUNTER_i
        for i in range(self.n_defense_types):
            hide_gene = f"HIDE_{i}"
            counter_gene = f"COUNTER_{i}"
            if prey.has(hide_gene) and not pred.has(counter_gene):
                base *= 0.6  # Каждая неконтрированная защита снижает шанс на 40%
            elif pred.has(counter_gene) and not prey.has(hide_gene):
                base += 0.05  # Лишняя атака немного помогает

        return min(max(base, 0.02), 0.8)

    def _act_prey(self, org):
        cell = self.resources[org.y][org.x]
        if org.has("SCAN"):
            gathered = min(cell, 2.5) * 0.6
        elif org.has("GATHER"):
            gathered = min(cell, 2.0) * 0.4
        else:
            gathered = min(cell, 1.5) * 0.25
        self.resources[org.y][org.x] -= gathered
        org.energy += gathered

    def _act_predator(self, org):
        # SPEED: двигаться к жертве
        if org.has("SPEED"):
            prey_here = [o for o in self.organisms
                        if o.role == "prey" and o.x == org.x and o.y == org.y
                        and o.energy > 0]
            if not prey_here:
                for nx, ny in self._neighbors(org.x, org.y):
                    prey_near = [o for o in self.organisms
                                if o.role == "prey" and o.x == nx and o.y == ny]
                    if prey_near:
                        org.x, org.y = nx, ny
                        org.energy -= 0.1
                        break

        prey_here = [o for o in self.organisms
                    if o.role == "prey" and o.x == org.x and o.y == org.y
                    and o.energy > 0]
        if not prey_here:
            return

        target = self.rng.choice(prey_here)
        catch_prob = self._catch_probability(org, target)

        if self.rng.random() < catch_prob:
            energy_gain = min(target.energy * 0.7, 5.0)
            org.energy += energy_gain
            target.energy = 0

    def _mutate(self, genome, role):
        genes = self.prey_genes if role == "prey" else self.pred_genes
        new = genome.copy()
        if self.rng.random() < self.mutation_rate and new:
            idx = self.rng.randint(0, len(new) - 1)
            new[idx] = self.rng.choice(genes)
        if self.rng.random() < self.mutation_rate * 0.5 and len(new) < self.max_genome:
            new.append(self.rng.choice(genes))
        if self.rng.random() < self.mutation_rate * 0.5 and len(new) > 1:
            new.pop(self.rng.randint(0, len(new) - 1))
        return new

    def step(self):
        self._produce_resources()
        self.rng.shuffle(self.organisms)

        for org in self.organisms:
            if org.role == "prey" and org.energy > 0:
                self._act_prey(org)

        for org in self.organisms:
            if org.role == "predator" and org.energy > 0:
                self._act_predator(org)

        for org in self.organisms:
            if org.role == "prey":
                cost = 0.4 + self.gene_cost * len(org.genome)
            else:
                cost = self.pred_base_cost + self.gene_cost * len(org.genome)
            org.energy -= cost * 0.7
            org.age += 1

        # Размножение
        new_orgs = []
        for org in self.organisms:
            threshold = 8.0 if org.role == "prey" else 10.0
            if org.energy > threshold and self.rng.random() < 0.25:
                nx, ny = self.rng.choice(self._neighbors(org.x, org.y))
                child = Organism(
                    x=nx, y=ny, energy=org.energy * 0.35,
                    genome=self._mutate(org.genome, org.role),
                    role=org.role, id=self._new_id()
                )
                org.energy *= 0.55
                new_orgs.append(child)

        self.organisms.extend(new_orgs)
        self.organisms = [o for o in self.organisms if o.energy > 0]

        max_pop = self.width * self.height * 3
        if len(self.organisms) > max_pop:
            self.organisms.sort(key=lambda o: o.energy)
            self.organisms = self.organisms[len(self.organisms) // 3:]

        self.step_num += 1

    def run(self, steps=800):
        for _ in range(steps):
            self.step()

    def result(self):
        prey = [o for o in self.organisms if o.role == "prey"]
        pred = [o for o in self.organisms if o.role == "predator"]
        prey_len = sum(o.complexity for o in prey) / len(prey) if prey else 0
        pred_len = sum(o.complexity for o in pred) / len(pred) if pred else 0
        prey_uniq = sum(o.unique_genes for o in prey) / len(prey) if prey else 0
        pred_uniq = sum(o.unique_genes for o in pred) / len(pred) if pred else 0
        return {
            "prey_n": len(prey), "pred_n": len(pred),
            "prey_len": round(prey_len, 2), "pred_len": round(pred_len, 2),
            "prey_uniq": round(prey_uniq, 2), "pred_uniq": round(pred_uniq, 2),
        }


def run_experiment():
    print("=" * 70)
    print("ПРОВЕРКА ФОРМУЛЫ: сложность = стоимость_ошибки × разнообразие_давлений")
    print("=" * 70)

    error_costs = [0.3, 0.6, 0.9]
    pressure_diversities = [2, 4, 6]
    n_seeds = 6

    # Матрица результатов
    results = {}

    print(f"\nЗапускаю {len(error_costs) * len(pressure_diversities) * n_seeds} симуляций...")

    for ec in error_costs:
        for pd in pressure_diversities:
            prey_lens = []
            pred_lens = []
            for seed in range(n_seeds):
                eco = ParameterizedEcosystem(
                    n_defense_types=pd,
                    pred_base_cost=ec,
                    seed=seed
                )
                eco.seed_population(100, 25)
                eco.run(800)
                r = eco.result()
                if r["prey_n"] > 5 and r["pred_n"] > 3:
                    prey_lens.append(r["prey_len"])
                    pred_lens.append(r["pred_len"])

            key = (ec, pd)
            if pred_lens:
                results[key] = {
                    "prey_len": sum(prey_lens) / len(prey_lens),
                    "pred_len": sum(pred_lens) / len(pred_lens),
                    "n_survived": len(pred_lens),
                }
            else:
                results[key] = {"prey_len": 0, "pred_len": 0, "n_survived": 0}

    # Таблица: сложность хищников
    print("\n\n--- Сложность ХИЩНИКОВ (avg genome length) ---")
    print(f"{'':>15}", end="")
    for pd in pressure_diversities:
        print(f"  diversity={pd:>2}", end="")
    print()

    for ec in error_costs:
        print(f"  error={ec:.1f}   ", end="")
        for pd in pressure_diversities:
            r = results.get((ec, pd), {})
            val = r.get("pred_len", 0)
            n = r.get("n_survived", 0)
            if n > 0:
                print(f"    {val:>5.2f} ({n})", end="")
            else:
                print(f"    ----- (0)", end="")
        print()

    # Таблица: сложность жертв
    print("\n\n--- Сложность ЖЕРТВ (avg genome length) ---")
    print(f"{'':>15}", end="")
    for pd in pressure_diversities:
        print(f"  diversity={pd:>2}", end="")
    print()

    for ec in error_costs:
        print(f"  error={ec:.1f}   ", end="")
        for pd in pressure_diversities:
            r = results.get((ec, pd), {})
            val = r.get("prey_len", 0)
            n = r.get("n_survived", 0)
            if n > 0:
                print(f"    {val:>5.2f} ({n})", end="")
            else:
                print(f"    ----- (0)", end="")
        print()

    # Анализ: мультипликативность
    print("\n\n--- Анализ: аддитивность vs мультипликативность ---")

    # Берём крайние точки
    low_low = results.get((0.3, 2), {}).get("pred_len", 0)
    low_high = results.get((0.3, 6), {}).get("pred_len", 0)
    high_low = results.get((0.9, 2), {}).get("pred_len", 0)
    high_high = results.get((0.9, 6), {}).get("pred_len", 0)

    print(f"  Pred complexity:")
    print(f"    (low_error, low_div):   {low_low:.2f}")
    print(f"    (low_error, high_div):  {low_high:.2f}")
    print(f"    (high_error, low_div):  {high_low:.2f}")
    print(f"    (high_error, high_div): {high_high:.2f}")

    if low_low > 0 and low_high > 0 and high_low > 0 and high_high > 0:
        # Аддитивная модель: C = a*E + b*D + c
        # Предсказание: high_high ≈ low_high + high_low - low_low
        additive_pred = low_high + high_low - low_low
        print(f"\n  Аддитивная предсказание: {additive_pred:.2f}")

        # Мультипликативная модель: C = k * E * D
        # Предсказание: high_high ≈ (low_high * high_low) / low_low
        if low_low > 0:
            mult_pred = (low_high * high_low) / low_low
            print(f"  Мультипликативная предсказание: {mult_pred:.2f}")

        print(f"  Реальное значение: {high_high:.2f}")

        err_add = abs(high_high - additive_pred)
        err_mult = abs(high_high - mult_pred) if low_low > 0 else float('inf')
        print(f"\n  Ошибка аддитивной: {err_add:.2f}")
        print(f"  Ошибка мультипликативной: {err_mult:.2f}")

        if err_mult < err_add:
            print("  → Данные лучше согласуются с МУЛЬТИПЛИКАТИВНОЙ моделью")
        elif err_add < err_mult:
            print("  → Данные лучше согласуются с АДДИТИВНОЙ моделью")
        else:
            print("  → Модели неразличимы")

    # Эффект каждого фактора отдельно
    print("\n\n--- Эффект каждого фактора ---")

    # Эффект error_cost (при фиксированном diversity=4)
    print("  Error cost (diversity=4):")
    for ec in error_costs:
        r = results.get((ec, 4), {})
        print(f"    error={ec:.1f}: pred={r.get('pred_len', 0):.2f}, prey={r.get('prey_len', 0):.2f}")

    # Эффект diversity (при фиксированном error=0.6)
    print("  Pressure diversity (error=0.6):")
    for pd in pressure_diversities:
        r = results.get((0.6, pd), {})
        print(f"    diversity={pd}: pred={r.get('pred_len', 0):.2f}, prey={r.get('prey_len', 0):.2f}")


if __name__ == "__main__":
    run_experiment()
