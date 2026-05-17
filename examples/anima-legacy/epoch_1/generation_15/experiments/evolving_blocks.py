"""
Эксперимент 3: Эволюция масштаба блоков

Вопрос: Может ли система сама найти оптимальный размер блока?

Эксп.2 показал: адаптивная система проваливается, потому что оптимизирует фитнес.
Здесь блок-размер — часть генома, эволюционирует вместе с содержанием.

Дизайн:
- Каждый агент имеет предпочтительный block_size (2..32)
- При размножении block_size наследуется с мутацией
- Отбор по двум критериям:
  A) только фитнес (контроль)
  B) только оригинальность
  C) фитнес + оригинальность (Парето)
  D) "любопытство" — отбор по оригинальности, но фитнес как порог выживания

Метрика: к какому block_size сходится каждый режим?
"""

import numpy as np
import json


def hamming_distance(a, b):
    return np.sum(a != b)


def originality(element, archive):
    if len(archive) == 0:
        return 1.0
    min_dist = min(hamming_distance(element, a) for a in archive)
    return min_dist / len(element)


def fitness(element):
    s = ''.join(map(str, element))
    return len([b for b in s.split('0') if len(b) >= 4])


class EvolvingAgent:
    def __init__(self, genome, block_size):
        self.genome = genome
        self.block_size = max(2, min(block_size, len(genome)))
        self.fitness_val = 0
        self.originality_val = 0

    def extract_blocks(self):
        bs = self.block_size
        n = len(self.genome) // bs
        return [self.genome[i*bs:(i+1)*bs] for i in range(n)]


def recombine_agents(parent1, parent2, mutation_rate=0.02):
    """Рекомбинация с учётом block_size родителей."""
    # наследуем block_size от случайного родителя + мутация
    bs = parent1.block_size if np.random.random() < 0.5 else parent2.block_size
    bs += np.random.choice([-2, -1, 0, 0, 0, 1, 2])  # мутация размера
    bs = max(2, min(bs, len(parent1.genome) // 2))

    # рекомбинация содержания на уровне block_size победителя
    n_blocks = len(parent1.genome) // bs
    child_genome = np.zeros_like(parent1.genome)

    for i in range(n_blocks):
        start = i * bs
        end = start + bs
        if np.random.random() < 0.5:
            child_genome[start:end] = parent1.genome[start:end]
        else:
            child_genome[start:end] = parent2.genome[start:end]

    # заполнить остаток (если есть)
    remainder = len(parent1.genome) - n_blocks * bs
    if remainder > 0:
        child_genome[-remainder:] = parent1.genome[-remainder:]

    # мутации
    mutations = np.random.random(len(child_genome)) < mutation_rate
    child_genome[mutations] = 1 - child_genome[mutations]

    return EvolvingAgent(child_genome, bs)


def run_mode(mode, n_agents=40, genome_size=64, n_generations=100, archive_window=50):
    """Один запуск одного режима."""
    # инициализация с разными block_size
    agents = []
    for _ in range(n_agents):
        genome = np.random.randint(0, 2, size=genome_size)
        bs = np.random.choice([2, 4, 8, 16, 32])
        agents.append(EvolvingAgent(genome, bs))

    archive = [a.genome.copy() for a in agents]
    bs_history = []
    orig_history = []
    fit_history = []

    for gen in range(n_generations):
        # оценить агентов
        for a in agents:
            a.fitness_val = fitness(a.genome)
            a.originality_val = originality(a.genome, archive[-archive_window:])

        # отбор зависит от режима
        if mode == 'fitness_only':
            scores = np.array([a.fitness_val for a in agents])
        elif mode == 'originality_only':
            scores = np.array([a.originality_val for a in agents])
        elif mode == 'pareto':
            # нормализованная сумма
            fit_arr = np.array([a.fitness_val for a in agents])
            orig_arr = np.array([a.originality_val for a in agents])
            fit_norm = (fit_arr - fit_arr.min()) / (fit_arr.max() - fit_arr.min() + 1e-10)
            orig_norm = (orig_arr - orig_arr.min()) / (orig_arr.max() - orig_arr.min() + 1e-10)
            scores = fit_norm + orig_norm
        elif mode == 'curiosity':
            # отбор по оригинальности, но с порогом фитнеса
            fit_arr = np.array([a.fitness_val for a in agents])
            orig_arr = np.array([a.originality_val for a in agents])
            median_fit = np.median(fit_arr)
            # те, кто ниже медианы фитнеса, получают штраф
            scores = orig_arr.copy()
            scores[fit_arr < median_fit * 0.5] *= 0.1
        else:
            raise ValueError(f"Unknown mode: {mode}")

        # запись статистик
        bs_vals = [a.block_size for a in agents]
        bs_history.append(np.mean(bs_vals))
        orig_history.append(np.mean([a.originality_val for a in agents]))
        fit_history.append(np.mean([a.fitness_val for a in agents]))

        # турнирный отбор + рекомбинация
        new_agents = []
        for _ in range(n_agents):
            t1 = np.random.choice(n_agents, 3, replace=True)
            t2 = np.random.choice(n_agents, 3, replace=True)
            p1 = agents[t1[np.argmax(scores[t1])]]
            p2 = agents[t2[np.argmax(scores[t2])]]
            child = recombine_agents(p1, p2)
            archive.append(child.genome.copy())
            new_agents.append(child)

        agents = new_agents

    return {
        'block_sizes': bs_history,
        'originality': orig_history,
        'fitness': fit_history,
        'final_bs_distribution': [a.block_size for a in agents]
    }


def run_experiment(n_runs=5):
    np.random.seed(42)
    modes = ['fitness_only', 'originality_only', 'pareto', 'curiosity']
    results = {m: {'block_sizes': [], 'originality': [], 'fitness': [], 'final_bs': []}
               for m in modes}

    for run in range(n_runs):
        for mode in modes:
            r = run_mode(mode)
            results[mode]['block_sizes'].append(r['block_sizes'])
            results[mode]['originality'].append(r['originality'])
            results[mode]['fitness'].append(r['fitness'])
            results[mode]['final_bs'].extend(r['final_bs_distribution'])

    return results


def analyze(results):
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 3: ЭВОЛЮЦИЯ МАСШТАБА БЛОКОВ")
    print("=" * 70)

    summary = {}
    for mode in ['fitness_only', 'originality_only', 'pareto', 'curiosity']:
        bs = np.array(results[mode]['block_sizes'])
        orig = np.array(results[mode]['originality'])
        fit = np.array(results[mode]['fitness'])
        final_bs = results[mode]['final_bs']

        late_bs = np.mean(bs[:, -20:])
        late_orig = np.mean(orig[:, -20:])
        late_fit = np.mean(fit[:, -20:])

        # распределение финальных block_size
        unique_bs, counts = np.unique(final_bs, return_counts=True)
        dominant_bs = unique_bs[np.argmax(counts)]
        diversity = len(unique_bs)

        print(f"\n--- {mode.upper()} ---")
        print(f"  Средний block_size (поздний): {late_bs:.1f}")
        print(f"  Доминантный block_size:        {dominant_bs}")
        print(f"  Разнообразие block_size:        {diversity} разных значений")
        print(f"  Оригинальность:                {late_orig:.4f}")
        print(f"  Фитнес:                        {late_fit:.2f}")
        print(f"  Распределение BS: ", end="")
        for b, c in sorted(zip(unique_bs, counts), key=lambda x: -x[1])[:5]:
            print(f"{b}({c})", end=" ")
        print()

        summary[mode] = {
            'mean_bs': float(late_bs),
            'dominant_bs': int(dominant_bs),
            'bs_diversity': int(diversity),
            'originality': float(late_orig),
            'fitness': float(late_fit)
        }

    # === Ключевой анализ ===
    print("\n" + "=" * 70)
    print("КЛЮЧЕВОЙ АНАЛИЗ: К ЧЕМУ СХОДИТСЯ КАЖДЫЙ РЕЖИМ?")
    print("=" * 70)

    for mode in ['fitness_only', 'originality_only', 'pareto', 'curiosity']:
        s = summary[mode]
        print(f"\n{mode}: BS→{s['mean_bs']:.0f}, orig={s['originality']:.3f}, fit={s['fitness']:.1f}")

    fit_bs = summary['fitness_only']['mean_bs']
    orig_bs = summary['originality_only']['mean_bs']
    pareto_bs = summary['pareto']['mean_bs']
    curio_bs = summary['curiosity']['mean_bs']

    print(f"\nФитнес тянет к BS={fit_bs:.0f}, оригинальность к BS={orig_bs:.0f}")

    if orig_bs < fit_bs:
        print("→ Подтверждено: новизна предпочитает МЕЛКИЕ блоки, качество — КРУПНЫЕ")
    if abs(curio_bs - orig_bs) < abs(curio_bs - fit_bs):
        print("→ 'Любопытство' сходится к масштабу новизны, не качества")
        print("   Порог фитнеса не мешает находить оптимальный масштаб порождения")

    # проверить, кто лучше по совокупности
    best_combined = max(summary.items(),
                        key=lambda x: x[1]['originality'] + x[1]['fitness'] / 10)
    print(f"\nЛучший баланс (orig + fit/10): {best_combined[0]}")

    return summary


if __name__ == '__main__':
    print("Запуск эксперимента 3...")
    results = run_experiment()
    summary = analyze(results)

    with open('experiments/evolving_blocks_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("\nРезультаты сохранены.")
