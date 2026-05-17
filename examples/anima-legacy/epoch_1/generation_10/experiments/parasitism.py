#!/usr/bin/env python3
"""
Паразитизм: симметричное давление отбора.

В эксперименте с хищник-жертвой давление было *асимметричным*:
хищник не поймал = умер, жертва потеряна = ну ладно, другие размножатся.

Здесь давление *симметрично*:
- Хозяин без иммунитета → заражён → теряет энергию → может умереть
- Паразит без подходящей атаки → голодает → умирает

Модель: matching game (замок-ключ).

Существуют N типов "замков" (иммунных рецепторов) и N типов "ключей" (антигенов).
- Хозяин имеет набор иммунных генов: IMMUNE_A, IMMUNE_B, IMMUNE_C, ...
- Паразит имеет набор атакующих генов: ATTACK_A, ATTACK_B, ATTACK_C, ...
- Паразит может заразить хозяина, если у паразита есть ATTACK_X,
  а у хозяина НЕТ соответствующего IMMUNE_X.
- Чем больше неприкрытых атак — тем сильнее инфекция.

Это классическая модель Красной Королевы:
- Если хозяева все имеют IMMUNE_A, паразитам выгодно потерять ATTACK_A (он бесполезен)
  и развить ATTACK_B.
- Тогда хозяевам нужен IMMUNE_B.
- Цикл продолжается.

Вопрос: растёт ли сложность *обеих* сторон одновременно?
"""

import random
import math
from collections import Counter


# 6 типов замков-ключей
N_TYPES = 6
IMMUNE_GENES = [f"IMMUNE_{chr(65+i)}" for i in range(N_TYPES)]  # A-F
ATTACK_GENES = [f"ATTACK_{chr(65+i)}" for i in range(N_TYPES)]  # A-F

# Дополнительные гены (не замок-ключ)
HOST_EXTRA = ["REPAIR", "TOLERATE"]  # Починка повреждений / Терпимость к паразиту
PARA_EXTRA = ["STEALTH", "VIRULENCE"]  # Скрытность / Агрессивность

ALL_HOST_GENES = IMMUNE_GENES + HOST_EXTRA
ALL_PARA_GENES = ATTACK_GENES + PARA_EXTRA

GENE_COST = 0.10  # Стоимость каждого гена


class Organism:
    __slots__ = ['x', 'y', 'energy', 'genome', 'role', 'age', 'id', 'infected_by']

    def __init__(self, x, y, energy, genome, role, id=0):
        self.x = x
        self.y = y
        self.energy = energy
        self.genome = genome
        self.role = role  # "host" or "parasite"
        self.age = 0
        self.id = id
        self.infected_by = []  # IDs of parasites currently infecting this host

    def has(self, gene):
        return gene in self.genome

    @property
    def immune_set(self):
        return {g for g in self.genome if g.startswith("IMMUNE_")}

    @property
    def attack_set(self):
        return {g for g in self.genome if g.startswith("ATTACK_")}

    @property
    def maintenance_cost(self):
        base = 0.40 if self.role == "host" else 0.30
        return base + GENE_COST * len(self.genome)

    @property
    def complexity(self):
        return len(self.genome)

    @property
    def unique_genes(self):
        return len(set(self.genome))


class ParasitismEcosystem:
    def __init__(self, width=30, height=30, seed=42,
                 mutation_rate=0.12, max_genome=10):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.step_num = 0
        self.next_id = 0
        self.mutation_rate = mutation_rate
        self.max_genome = max_genome
        self.organisms: list[Organism] = []
        self.history = []
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

    def seed_population(self, n_hosts=120, n_parasites=60):
        for _ in range(n_hosts):
            # Начальный геном: 1-3 случайных иммунных гена
            genome_len = self.rng.randint(1, 3)
            genome = [self.rng.choice(ALL_HOST_GENES) for _ in range(genome_len)]
            x = self.rng.randint(0, self.width - 1)
            y = self.rng.randint(0, self.height - 1)
            self.organisms.append(Organism(
                x=x, y=y, energy=6.0, genome=genome,
                role="host", id=self._new_id()
            ))

        for _ in range(n_parasites):
            genome_len = self.rng.randint(1, 3)
            genome = [self.rng.choice(ALL_PARA_GENES) for _ in range(genome_len)]
            x = self.rng.randint(0, self.width - 1)
            y = self.rng.randint(0, self.height - 1)
            self.organisms.append(Organism(
                x=x, y=y, energy=5.0, genome=genome,
                role="parasite", id=self._new_id()
            ))

    def _produce_resources(self):
        for y in range(self.height):
            for x in range(self.width):
                self.resources[y][x] = min(
                    self.resources[y][x] + 1.0 + self.rng.random() * 0.5,
                    8.0
                )

    def _infection_strength(self, parasite, host):
        """Сила заражения: сколько атак паразита не прикрыты иммунитетом хозяина."""
        attacks = parasite.attack_set
        immunes = host.immune_set

        # Маппинг: ATTACK_A ↔ IMMUNE_A
        unblocked = 0
        total_attacks = 0
        for atk in attacks:
            letter = atk.split("_")[1]
            matching_immune = f"IMMUNE_{letter}"
            total_attacks += 1
            if not host.has(matching_immune):
                unblocked += 1

        if total_attacks == 0:
            return 0.0

        # Базовая сила: каждая неприкрытая атака даёт полную долю
        strength = unblocked * 0.35

        # STEALTH: повышает шанс заражения
        if parasite.has("STEALTH"):
            strength += 0.15

        # VIRULENCE: больше урона
        if parasite.has("VIRULENCE"):
            strength *= 1.5

        # TOLERATE: хозяин снижает урон от инфекции
        if host.has("TOLERATE"):
            strength *= 0.6

        return min(strength, 1.5)

    def _act_host(self, org):
        """Хозяин: собирает ресурсы."""
        cell_val = self.resources[org.y][org.x]
        gathered = min(cell_val, 2.0) * 0.55
        self.resources[org.y][org.x] -= gathered
        org.energy += gathered

        # REPAIR: восстановление от инфекции
        if org.has("REPAIR") and org.energy < 5.0:
            org.energy += 0.25

    def _act_parasite(self, org):
        """Паразит: собирает немного ресурсов + заражает хозяев для бонуса."""
        # Паразиты имеют базовый сбор (свободноживущая фаза)
        cell_val = self.resources[org.y][org.x]
        gathered = min(cell_val, 1.2) * 0.3
        self.resources[org.y][org.x] -= gathered
        org.energy += gathered

        # Поиск хозяина для инфекции (бонусная энергия)
        hosts_here = [o for o in self.organisms
                     if o.role == "host" and o.x == org.x and o.y == org.y
                     and o.energy > 1.0]

        if not hosts_here:
            # Ищем хозяина в соседних клетках
            for nx, ny in self._neighbors(org.x, org.y):
                hosts_near = [o for o in self.organisms
                            if o.role == "host" and o.x == nx and o.y == ny
                            and o.energy > 1.0]
                if hosts_near:
                    org.x, org.y = nx, ny
                    org.energy -= 0.08
                    hosts_here = hosts_near
                    break

        if not hosts_here:
            return

        # Выбрать хозяина (предпочитаем того, кого легче заразить)
        target = max(hosts_here,
                    key=lambda h: self._infection_strength(org, h))

        strength = self._infection_strength(org, target)

        if strength > 0.05 and self.rng.random() < 0.5:
            # Успешное заражение — умеренный урон
            energy_drain = min(strength * 1.5, target.energy * 0.3)
            target.energy -= energy_drain
            org.energy += energy_drain * 0.8

    def _mutate_genome(self, genome, role):
        genes = ALL_HOST_GENES if role == "host" else ALL_PARA_GENES
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

        # Хозяева собирают ресурсы
        for org in self.organisms:
            if org.role == "host" and org.energy > 0:
                self._act_host(org)

        # Паразиты атакуют
        for org in self.organisms:
            if org.role == "parasite" and org.energy > 0:
                self._act_parasite(org)

        # Затраты
        for org in self.organisms:
            org.energy -= org.maintenance_cost * 0.7
            org.age += 1

        # Размножение
        new_organisms = []
        for org in self.organisms:
            threshold = 7.0 if org.role == "host" else 6.0
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
        hosts = [o for o in self.organisms if o.role == "host"]
        paras = [o for o in self.organisms if o.role == "parasite"]

        def stats(organisms, gene_list):
            if not organisms:
                return {"count": 0, "avg_complexity": 0, "avg_unique": 0,
                        "gene_prevalence": {}, "top_genomes": [],
                        "immune_diversity": 0, "attack_diversity": 0}
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

            # Разнообразие иммунных/атакующих профилей (уникальных комбинаций)
            if organisms[0].role == "host":
                profiles = Counter(frozenset(o.immune_set) for o in organisms)
            else:
                profiles = Counter(frozenset(o.attack_set) for o in organisms)
            profile_diversity = len(profiles)

            return {
                "count": n,
                "avg_complexity": round(avg_c, 2),
                "avg_unique": round(avg_u, 2),
                "gene_prevalence": prevalence,
                "top_genomes": top_genomes,
                "profile_diversity": profile_diversity,
            }

        self.history.append({
            "step": self.step_num,
            "host": stats(hosts, ALL_HOST_GENES),
            "parasite": stats(paras, ALL_PARA_GENES),
        })

    def run(self, steps=600):
        self._record()
        for _ in range(steps):
            self.step()
            hosts_alive = any(o.role == "host" for o in self.organisms)
            paras_alive = any(o.role == "parasite" for o in self.organisms)
            if not hosts_alive or not paras_alive:
                break
        return self.history


def print_snapshot(label, h):
    host = h["host"]
    para = h["parasite"]
    print(f"  {label}: host={host['count']:>4} (len={host['avg_complexity']:.2f}, "
          f"profiles={host['profile_diversity']}) | "
          f"para={para['count']:>4} (len={para['avg_complexity']:.2f}, "
          f"profiles={para['profile_diversity']})")


def run_experiment():
    print("=" * 70)
    print("ПАРАЗИТИЗМ: СИММЕТРИЧНОЕ ДАВЛЕНИЕ ОТБОРА")
    print("=" * 70)

    # Эксперимент 1: Динамика коэволюции
    print("\n--- Эксперимент 1: Динамика (3 seed, 1200 шагов) ---")
    for seed in range(3):
        print(f"\n  seed={seed}:")
        eco = ParasitismEcosystem(seed=seed)
        eco.seed_population(120, 60)
        eco.run(1200)

        checkpoints = [0, 100, 200, 400, 600, 800, 1000, 1200]
        for step in checkpoints:
            if step < len(eco.history):
                print_snapshot(f"step={step:>4}", eco.history[step])

        h0 = eco.history[0]
        hf = eco.history[-1]
        print(f"  ИТОГ: host {h0['host']['avg_complexity']:.2f} → {hf['host']['avg_complexity']:.2f} | "
              f"para {h0['parasite']['avg_complexity']:.2f} → {hf['parasite']['avg_complexity']:.2f}")

    # Эксперимент 2: Сравнение с контролем (без паразитов)
    print("\n\n--- Эксперимент 2: С паразитами vs без (8 seeds) ---")
    para_lens = []
    host_lens_with = []
    host_lens_without = []

    for seed in range(8):
        eco = ParasitismEcosystem(seed=seed)
        eco.seed_population(120, 60)
        eco.run(1000)
        hf = eco.history[-1]
        if hf["host"]["count"] > 0:
            host_lens_with.append(hf["host"]["avg_complexity"])
        if hf["parasite"]["count"] > 0:
            para_lens.append(hf["parasite"]["avg_complexity"])

        eco_ctrl = ParasitismEcosystem(seed=seed)
        eco_ctrl.seed_population(120, 0)
        eco_ctrl.run(1000)
        hf_ctrl = eco_ctrl.history[-1]
        if hf_ctrl["host"]["count"] > 0:
            host_lens_without.append(hf_ctrl["host"]["avg_complexity"])

    if host_lens_with and host_lens_without:
        print(f"  С паразитами:  host len = {sum(host_lens_with)/len(host_lens_with):.2f}")
        print(f"  Без паразитов: host len = {sum(host_lens_without)/len(host_lens_without):.2f}")
        diff = sum(host_lens_with)/len(host_lens_with) - sum(host_lens_without)/len(host_lens_without)
        print(f"  Разница: {diff:+.2f}")
    if para_lens:
        print(f"  Паразиты:      para len = {sum(para_lens)/len(para_lens):.2f}")

    # Эксперимент 3: Красная Королева — циклы доминирования
    print("\n\n--- Эксперимент 3: Красная Королева (иммунные/атакующие профили) ---")
    eco = ParasitismEcosystem(seed=42)
    eco.seed_population(150, 75)
    eco.run(1200)

    print(f"\n  {'step':>5} | {'host':>40} | {'para':>40}")
    print("  " + "-" * 90)

    for step in [0, 100, 200, 300, 400, 600, 800, 1000, 1200]:
        if step < len(eco.history):
            h = eco.history[step]
            hp = h["host"]["gene_prevalence"]
            pp = h["parasite"]["gene_prevalence"]
            # Показываем только иммунные/атакующие гены
            host_imm = " ".join(f"{chr(65+i)}:{hp.get(f'IMMUNE_{chr(65+i)}', 0):>4.0f}%"
                               for i in range(N_TYPES))
            para_atk = " ".join(f"{chr(65+i)}:{pp.get(f'ATTACK_{chr(65+i)}', 0):>4.0f}%"
                               for i in range(N_TYPES))
            print(f"  {step:>5} | {host_imm} | {para_atk}")

    # Эксперимент 4: Сравнение с хищник-жертвой (асимметрия vs симметрия)
    print("\n\n--- Эксперимент 4: Асимметрия коэволюции ---")
    print("  (Сравниваем рост сложности хищник-жертвы vs хозяин-паразит)")
    print(f"\n  {'модель':>20} | {'сторона A':>20} | {'сторона B':>20} | {'ratio':>6}")
    print("  " + "-" * 75)

    # Запускаем оба типа для сравнения
    from coevolution import CoevolutionaryEcosystem

    pred_lens = []
    prey_lens = []
    host_lens = []
    par_lens = []

    for seed in range(8):
        # Хищник-жертва
        eco_pv = CoevolutionaryEcosystem(seed=seed)
        eco_pv.seed_population(120, 30)
        eco_pv.run(800)
        hf = eco_pv.history[-1]
        if hf["prey"]["count"] > 0 and hf["predator"]["count"] > 0:
            prey_lens.append(hf["prey"]["avg_complexity"])
            pred_lens.append(hf["predator"]["avg_complexity"])

        # Хозяин-паразит
        eco_hp = ParasitismEcosystem(seed=seed)
        eco_hp.seed_population(120, 60)
        eco_hp.run(800)
        hf = eco_hp.history[-1]
        if hf["host"]["count"] > 0 and hf["parasite"]["count"] > 0:
            host_lens.append(hf["host"]["avg_complexity"])
            par_lens.append(hf["parasite"]["avg_complexity"])

    if prey_lens and pred_lens:
        avg_prey = sum(prey_lens) / len(prey_lens)
        avg_pred = sum(pred_lens) / len(pred_lens)
        ratio_pv = avg_pred / avg_prey if avg_prey > 0 else 0
        print(f"  {'хищник-жертва':>20} | prey={avg_prey:>14.2f} | pred={avg_pred:>14.2f} | {ratio_pv:>5.2f}x")

    if host_lens and par_lens:
        avg_host = sum(host_lens) / len(host_lens)
        avg_par = sum(par_lens) / len(par_lens)
        ratio_hp = avg_par / avg_host if avg_host > 0 else 0
        print(f"  {'хозяин-паразит':>20} | host={avg_host:>14.2f} | para={avg_par:>14.2f} | {ratio_hp:>5.2f}x")

    print()
    if prey_lens and pred_lens and host_lens and par_lens:
        print(f"  Хищник/жертва ratio: {ratio_pv:.2f}x (асимметрия)")
        print(f"  Паразит/хозяин ratio: {ratio_hp:.2f}x")
        if abs(ratio_hp - 1.0) < abs(ratio_pv - 1.0):
            print("  → Паразитизм более СИММЕТРИЧЕН, чем хищничество")
        else:
            print("  → Паразитизм НЕ более симметричен")


if __name__ == "__main__":
    run_experiment()
