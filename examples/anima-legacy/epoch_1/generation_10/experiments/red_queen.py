#!/usr/bin/env python3
"""
Красная Королева: matching game между хозяевами и паразитами.

Упрощённая модель (well-mixed, без пространства):
- N хозяев с иммунными генотипами (набор типов A-F)
- M паразитов с атакующими генотипами (набор типов A-F)
- Каждый ход: каждый хозяин с вероятностью p встречает случайного паразита
- Паразит успешно заражает, если у него есть атака, которую хозяин не блокирует
- Урон пропорционален числу неприкрытых атак
- Хозяева получают фиксированный доход
- Оба размножаются с мутациями

Ключевая идея: сосуществование обеспечивается тем, что паразиты ЗАВИСЯТ от хозяев,
а хозяева несут НЕИЗБЕЖНЫЙ урон (каждый встречает паразитов). Вопрос не "быть ли заражённым",
а "насколько сильно".
"""

import random
import math
from collections import Counter


N_TYPES = 6
LETTERS = [chr(65 + i) for i in range(N_TYPES)]  # A-F

GENE_COST = 0.08  # Стоимость за каждый ген в геноме


class Organism:
    __slots__ = ['energy', 'genome', 'role', 'age', 'id']

    def __init__(self, energy, genome, role, id=0):
        self.energy = energy
        self.genome = genome  # list of letters (A-F)
        self.role = role
        self.age = 0
        self.id = id

    @property
    def gene_set(self):
        return set(self.genome)

    @property
    def complexity(self):
        return len(self.genome)

    @property
    def unique_genes(self):
        return len(set(self.genome))

    @property
    def maintenance_cost(self):
        base = 0.3 if self.role == "host" else 0.25
        return base + GENE_COST * len(self.genome)


class RedQueenModel:
    def __init__(self, seed=42, encounter_rate=0.4,
                 mutation_rate=0.15, max_genome=8,
                 host_income=1.2, infection_damage=1.5,
                 parasite_gain=0.8):
        self.rng = random.Random(seed)
        self.step_num = 0
        self.next_id = 0
        self.encounter_rate = encounter_rate
        self.mutation_rate = mutation_rate
        self.max_genome = max_genome
        self.host_income = host_income
        self.infection_damage = infection_damage
        self.parasite_gain = parasite_gain
        self.organisms: list[Organism] = []
        self.history = []

    def _new_id(self):
        self.next_id += 1
        return self.next_id

    def seed_population(self, n_hosts=200, n_parasites=100):
        for _ in range(n_hosts):
            n_genes = self.rng.randint(1, 3)
            genome = [self.rng.choice(LETTERS) for _ in range(n_genes)]
            self.organisms.append(Organism(
                energy=5.0, genome=genome, role="host", id=self._new_id()
            ))
        for _ in range(n_parasites):
            n_genes = self.rng.randint(1, 3)
            genome = [self.rng.choice(LETTERS) for _ in range(n_genes)]
            self.organisms.append(Organism(
                energy=4.0, genome=genome, role="parasite", id=self._new_id()
            ))

    def _infection_score(self, parasite, host):
        """Число атак паразита, не прикрытых иммунитетом хозяина."""
        p_set = parasite.gene_set
        h_set = host.gene_set
        unblocked = p_set - h_set  # Атаки, которых нет в иммунитете
        return len(unblocked)

    def _mutate(self, genome):
        new = genome.copy()

        # Точечная мутация
        if self.rng.random() < self.mutation_rate and new:
            idx = self.rng.randint(0, len(new) - 1)
            new[idx] = self.rng.choice(LETTERS)

        # Дупликация
        if self.rng.random() < self.mutation_rate * 0.4 and len(new) < self.max_genome:
            new.append(self.rng.choice(LETTERS))

        # Делеция
        if self.rng.random() < self.mutation_rate * 0.4 and len(new) > 1:
            idx = self.rng.randint(0, len(new) - 1)
            new.pop(idx)

        return new

    def step(self):
        hosts = [o for o in self.organisms if o.role == "host"]
        parasites = [o for o in self.organisms if o.role == "parasite"]

        if not hosts or not parasites:
            self.step_num += 1
            self._record()
            return

        # 1. Хозяева получают доход
        for h in hosts:
            h.energy += self.host_income

        # 2. Встречи: каждый хозяин с вероятностью encounter_rate встречает паразита
        for h in hosts:
            if self.rng.random() < self.encounter_rate:
                p = self.rng.choice(parasites)
                score = self._infection_score(p, h)
                if score > 0:
                    damage = score * self.infection_damage
                    h.energy -= damage
                    p.energy += score * self.parasite_gain

        # 3. Затраты
        for o in self.organisms:
            o.energy -= o.maintenance_cost
            o.age += 1

        # 4. Размножение
        new_organisms = []
        for o in self.organisms:
            threshold = 6.0 if o.role == "host" else 5.0
            if o.energy > threshold and self.rng.random() < 0.3:
                child = Organism(
                    energy=o.energy * 0.35,
                    genome=self._mutate(o.genome),
                    role=o.role,
                    id=self._new_id()
                )
                o.energy *= 0.55
                new_organisms.append(child)

        self.organisms.extend(new_organisms)

        # 5. Смерть
        self.organisms = [o for o in self.organisms if o.energy > 0]

        # 6. Carrying capacity (мягкое)
        hosts = [o for o in self.organisms if o.role == "host"]
        parasites = [o for o in self.organisms if o.role == "parasite"]
        max_hosts = 2000
        max_para = 1000
        if len(hosts) > max_hosts:
            self.rng.shuffle(hosts)
            hosts = sorted(hosts, key=lambda o: o.energy)[len(hosts) - max_hosts:]
        if len(parasites) > max_para:
            self.rng.shuffle(parasites)
            parasites = sorted(parasites, key=lambda o: o.energy)[len(parasites) - max_para:]
        self.organisms = hosts + parasites

        self.step_num += 1
        self._record()

    def _record(self):
        hosts = [o for o in self.organisms if o.role == "host"]
        paras = [o for o in self.organisms if o.role == "parasite"]

        def stats(organisms):
            if not organisms:
                return {"count": 0, "avg_len": 0, "avg_unique": 0,
                        "type_prevalence": {}, "top_genomes": [],
                        "profile_diversity": 0}
            n = len(organisms)
            avg_len = sum(o.complexity for o in organisms) / n
            avg_uniq = sum(o.unique_genes for o in organisms) / n

            type_counts = Counter()
            for o in organisms:
                for g in o.gene_set:
                    type_counts[g] += 1
            prevalence = {l: round(type_counts.get(l, 0) / n * 100, 1) for l in LETTERS}

            genome_strs = Counter("|".join(sorted(o.genome)) for o in organisms)
            top = genome_strs.most_common(5)
            top_genomes = [(g, c, round(c / n * 100, 1)) for g, c in top]

            profiles = Counter(frozenset(o.gene_set) for o in organisms)
            profile_div = len(profiles)

            return {
                "count": n, "avg_len": round(avg_len, 2),
                "avg_unique": round(avg_uniq, 2),
                "type_prevalence": prevalence,
                "top_genomes": top_genomes,
                "profile_diversity": profile_div,
            }

        self.history.append({
            "step": self.step_num,
            "host": stats(hosts),
            "parasite": stats(paras),
        })

    def run(self, steps=800):
        self._record()
        for _ in range(steps):
            self.step()
            hosts = any(o.role == "host" for o in self.organisms)
            paras = any(o.role == "parasite" for o in self.organisms)
            if not hosts or not paras:
                break
        return self.history


def fmt(h, role):
    s = h[role]
    return f"n={s['count']:>4} len={s['avg_len']:.2f} uniq={s['avg_unique']:.2f} profiles={s['profile_diversity']:>3}"


def run_experiment():
    print("=" * 70)
    print("КРАСНАЯ КОРОЛЕВА: MATCHING GAME")
    print("=" * 70)

    # Эксперимент 1: Динамика
    print("\n--- Эксперимент 1: Динамика (5 seeds, 1500 шагов) ---")
    all_host_final = []
    all_para_final = []

    for seed in range(5):
        model = RedQueenModel(seed=seed)
        model.seed_population(200, 100)
        model.run(1500)

        print(f"\n  seed={seed}:")
        checkpoints = [0, 100, 300, 500, 800, 1000, 1500]
        for step in checkpoints:
            if step < len(model.history):
                h = model.history[step]
                print(f"    step={step:>4}: host [{fmt(h, 'host')}] | para [{fmt(h, 'parasite')}]")

        hf = model.history[-1]
        if hf["host"]["count"] > 0:
            all_host_final.append(hf["host"]["avg_len"])
        if hf["parasite"]["count"] > 0:
            all_para_final.append(hf["parasite"]["avg_len"])

        h0 = model.history[0]
        hf = model.history[-1]
        extinct = ""
        if hf["host"]["count"] == 0:
            extinct = " [HOSTS EXTINCT]"
        elif hf["parasite"]["count"] == 0:
            extinct = " [PARASITES EXTINCT]"
        print(f"    ИТОГ: host {h0['host']['avg_len']:.2f}→{hf['host']['avg_len']:.2f} | "
              f"para {h0['parasite']['avg_len']:.2f}→{hf['parasite']['avg_len']:.2f}{extinct}")

    # Эксперимент 2: Контроль — без паразитов
    print("\n\n--- Эксперимент 2: С паразитами vs без (10 seeds) ---")
    with_para = []
    without_para = []

    for seed in range(10):
        # С паразитами
        m = RedQueenModel(seed=seed)
        m.seed_population(200, 100)
        m.run(1000)
        hf = m.history[-1]
        if hf["host"]["count"] > 10:
            with_para.append(hf["host"]["avg_len"])

        # Без паразитов
        m2 = RedQueenModel(seed=seed)
        m2.seed_population(200, 0)
        m2.run(1000)
        hf2 = m2.history[-1]
        if hf2["host"]["count"] > 10:
            without_para.append(hf2["host"]["avg_len"])

    if with_para:
        print(f"  С паразитами:  host len = {sum(with_para)/len(with_para):.2f} (n={len(with_para)} survived)")
    if without_para:
        print(f"  Без паразитов: host len = {sum(without_para)/len(without_para):.2f} (n={len(without_para)} survived)")
    if with_para and without_para:
        diff = sum(with_para)/len(with_para) - sum(without_para)/len(without_para)
        print(f"  Разница: {diff:+.2f}")

    # Эксперимент 3: Red Queen dynamics — типы по времени
    print("\n\n--- Эксперимент 3: Типы A-F по времени ---")
    m = RedQueenModel(seed=7)
    m.seed_population(250, 120)
    m.run(1500)

    print(f"  {'step':>5} | {'host types':>40} | {'para types':>40}")
    print("  " + "-" * 90)
    for step in [0, 100, 200, 300, 500, 700, 1000, 1200, 1500]:
        if step < len(m.history):
            h = m.history[step]
            hp = h["host"]["type_prevalence"]
            pp = h["parasite"]["type_prevalence"]
            host_str = " ".join(f"{l}:{hp.get(l,0):>4.0f}%" for l in LETTERS)
            para_str = " ".join(f"{l}:{pp.get(l,0):>4.0f}%" for l in LETTERS)
            hn = h['host']['count']
            pn = h['parasite']['count']
            print(f"  {step:>5} | {host_str} ({hn:>4}) | {para_str} ({pn:>4})")

    # Эксперимент 4: Асимметрия — сравнение host vs parasite complexity
    print("\n\n--- Эксперимент 4: Симметричность сложности (20 seeds) ---")
    host_finals = []
    para_finals = []

    for seed in range(20):
        m = RedQueenModel(seed=seed)
        m.seed_population(200, 100)
        m.run(1000)
        hf = m.history[-1]
        if hf["host"]["count"] > 10 and hf["parasite"]["count"] > 5:
            host_finals.append(hf["host"]["avg_len"])
            para_finals.append(hf["parasite"]["avg_len"])

    if host_finals and para_finals:
        avg_h = sum(host_finals) / len(host_finals)
        avg_p = sum(para_finals) / len(para_finals)
        ratio = avg_p / avg_h if avg_h > 0 else 0
        print(f"  Выжили обе стороны: {len(host_finals)} из 20 запусков")
        print(f"  Host avg len:     {avg_h:.2f}")
        print(f"  Parasite avg len: {avg_p:.2f}")
        print(f"  Ratio (para/host): {ratio:.2f}x")
        if 0.8 < ratio < 1.25:
            print("  → Сложность растёт СИММЕТРИЧНО")
        elif ratio >= 1.25:
            print("  → Паразиты сложнее (как хищники в пред. эксперименте)")
        else:
            print("  → Хозяева сложнее")
    else:
        print(f"  Обе стороны выжили в {len(host_finals)} запусках — недостаточно данных")
        if all_host_final:
            print(f"  Host final (all): {sum(all_host_final)/len(all_host_final):.2f}")
        if all_para_final:
            print(f"  Para final (all): {sum(all_para_final)/len(all_para_final):.2f}")


if __name__ == "__main__":
    run_experiment()
