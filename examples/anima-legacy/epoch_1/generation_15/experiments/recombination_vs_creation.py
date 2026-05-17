"""
Эксперимент 1: Рекомбинация vs Порождение

Вопрос: когда рекомбинация перестаёт быть перестановкой и становится порождением?

Три режима генерации новых элементов:
1. Случайная рекомбинация (flat crossover + mutation)
2. Направленная рекомбинация (с отбором по фитнесу)
3. Иерархическая рекомбинация (элементы → блоки → мета-блоки)

Метрика: "оригинальность" = min расстояние Хэмминга до всех предшественников,
нормализованное на длину строки.

Дополнительная метрика: "несводимость" = сжимаемость нового элемента
относительно архива предшественников (через LZ-подобную компрессию).
"""

import numpy as np
from collections import defaultdict
import zlib
import json


def hamming_distance(a, b):
    return np.sum(a != b)


def originality(element, archive):
    """Минимальное расстояние до ближайшего предшественника, нормализованное."""
    if len(archive) == 0:
        return 1.0
    min_dist = min(hamming_distance(element, a) for a in archive)
    return min_dist / len(element)


def compressibility_ratio(element, archive):
    """Насколько элемент сжимается, если добавить его к архиву.
    Низкое значение = элемент несёт мало новой информации."""
    elem_bytes = element.tobytes()
    if len(archive) == 0:
        compressed_alone = len(zlib.compress(elem_bytes))
        return compressed_alone / len(elem_bytes)

    archive_bytes = b''.join(a.tobytes() for a in archive[-50:])  # последние 50
    compressed_archive = len(zlib.compress(archive_bytes))
    compressed_with = len(zlib.compress(archive_bytes + elem_bytes))
    marginal = compressed_with - compressed_archive
    return marginal / len(elem_bytes)


# === Режим 1: Случайная рекомбинация ===

def random_recombination(pop, mutation_rate=0.02):
    """Случайный кроссовер двух родителей + точечные мутации."""
    p1, p2 = pop[np.random.choice(len(pop), 2, replace=False)]
    mask = np.random.randint(0, 2, size=len(p1)).astype(bool)
    child = np.where(mask, p1, p2)
    mutations = np.random.random(len(child)) < mutation_rate
    child[mutations] = 1 - child[mutations]
    return child


# === Режим 2: Направленная рекомбинация ===

def fitness(element):
    """Фитнес = количество блоков из 4+ подряд идущих единиц."""
    s = ''.join(map(str, element))
    blocks = [b for b in s.split('0') if len(b) >= 4]
    return len(blocks)


def directed_recombination(pop, mutation_rate=0.02):
    """Турнирный отбор + кроссовер + мутация."""
    fitnesses = np.array([fitness(p) for p in pop])
    # турнир из 3
    candidates = np.random.choice(len(pop), 6, replace=True)
    t1 = candidates[:3]
    t2 = candidates[3:]
    p1 = pop[t1[np.argmax(fitnesses[t1])]]
    p2 = pop[t2[np.argmax(fitnesses[t2])]]

    # двуточечный кроссовер
    points = sorted(np.random.choice(len(p1), 2, replace=False))
    child = p1.copy()
    child[points[0]:points[1]] = p2[points[0]:points[1]]

    mutations = np.random.random(len(child)) < mutation_rate
    child[mutations] = 1 - child[mutations]
    return child


# === Режим 3: Иерархическая рекомбинация ===

class HierarchicalGenerator:
    def __init__(self, element_size, block_size=8):
        self.element_size = element_size
        self.block_size = block_size
        self.n_blocks = element_size // block_size
        self.block_library = {}  # блоки, доказавшие ценность

    def extract_blocks(self, element):
        """Разбить элемент на блоки."""
        return [element[i*self.block_size:(i+1)*self.block_size]
                for i in range(self.n_blocks)]

    def update_library(self, pop):
        """Добавить лучшие блоки в библиотеку."""
        for elem in pop:
            blocks = self.extract_blocks(elem)
            f = fitness(elem)
            for i, block in enumerate(blocks):
                key = tuple(block)
                if key not in self.block_library or self.block_library[key] < f:
                    self.block_library[key] = f

        # оставить только топ-100 блоков
        if len(self.block_library) > 100:
            sorted_blocks = sorted(self.block_library.items(), key=lambda x: -x[1])
            self.block_library = dict(sorted_blocks[:100])

    def generate(self, pop, mutation_rate=0.02):
        """Собрать элемент из блоков библиотеки + мутация."""
        self.update_library(pop)

        child = np.zeros(self.element_size, dtype=int)
        library_blocks = list(self.block_library.keys())

        for i in range(self.n_blocks):
            if library_blocks and np.random.random() < 0.7:
                # взять блок из библиотеки
                block = np.array(library_blocks[np.random.randint(len(library_blocks))])
            else:
                # случайный блок
                parent = pop[np.random.randint(len(pop))]
                block = self.extract_blocks(parent)[i].copy()
            child[i*self.block_size:(i+1)*self.block_size] = block

        # мутация
        mutations = np.random.random(len(child)) < mutation_rate
        child[mutations] = 1 - child[mutations]
        return child


# === Основной эксперимент ===

def run_experiment(n_elements=32, element_size=64, n_generations=100, n_runs=5):
    np.random.seed(42)
    results = {mode: {'originality': [], 'compressibility': [], 'fitness': [], 'jumps': []}
               for mode in ['random', 'directed', 'hierarchical']}

    for run in range(n_runs):
        for mode in ['random', 'directed', 'hierarchical']:
            pop = np.random.randint(0, 2, size=(n_elements, element_size))
            archive = [p.copy() for p in pop]
            hier = HierarchicalGenerator(element_size) if mode == 'hierarchical' else None

            orig_history = []
            comp_history = []
            fit_history = []

            for gen in range(n_generations):
                new_pop = []
                gen_orig = []
                gen_comp = []

                for _ in range(n_elements):
                    if mode == 'random':
                        child = random_recombination(pop)
                    elif mode == 'directed':
                        child = directed_recombination(pop)
                    else:
                        child = hier.generate(pop)

                    o = originality(child, archive[-50:])  # сравнивать с последними 50
                    c = compressibility_ratio(child, archive[-50:])
                    gen_orig.append(o)
                    gen_comp.append(c)
                    new_pop.append(child)
                    archive.append(child.copy())

                pop = np.array(new_pop)
                orig_history.append(np.mean(gen_orig))
                comp_history.append(np.mean(gen_comp))
                fit_history.append(np.mean([fitness(p) for p in pop]))

            results[mode]['originality'].append(orig_history)
            results[mode]['compressibility'].append(comp_history)
            results[mode]['fitness'].append(fit_history)

            # Найти "скачки" — поколения, где оригинальность выросла > 2 стд от среднего
            orig_arr = np.array(orig_history)
            diffs = np.diff(orig_arr)
            mean_diff = np.mean(diffs)
            std_diff = np.std(diffs) if np.std(diffs) > 0 else 1e-10
            jumps = np.where(diffs > mean_diff + 2 * std_diff)[0]
            results[mode]['jumps'].append(len(jumps))

    return results


def analyze(results):
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 1: РЕКОМБИНАЦИЯ VS ПОРОЖДЕНИЕ")
    print("=" * 70)

    for mode in ['random', 'directed', 'hierarchical']:
        orig = np.array(results[mode]['originality'])
        comp = np.array(results[mode]['compressibility'])
        fit = np.array(results[mode]['fitness'])
        jumps = results[mode]['jumps']

        print(f"\n--- {mode.upper()} ---")
        print(f"Оригинальность (среднее по последним 50 поколениям):")
        print(f"  mean: {np.mean(orig[:, -50:]):.4f}")
        print(f"  std:  {np.std(orig[:, -50:]):.4f}")

        print(f"Маргинальная компрессируемость (последние 50):")
        print(f"  mean: {np.mean(comp[:, -50:]):.4f}")

        print(f"Фитнес (последние 50):")
        print(f"  mean: {np.mean(fit[:, -50:]):.4f}")

        print(f"Скачки оригинальности (>2σ):")
        print(f"  mean: {np.mean(jumps):.1f}")

        # тренд оригинальности: растёт или падает?
        mean_orig = np.mean(orig, axis=0)
        first_quarter = np.mean(mean_orig[:50])
        last_quarter = np.mean(mean_orig[-50:])
        trend = "РАСТЁТ" if last_quarter > first_quarter * 1.05 else \
                "ПАДАЕТ" if last_quarter < first_quarter * 0.95 else "СТАБИЛЬНА"
        print(f"Тренд оригинальности: {trend} ({first_quarter:.4f} → {last_quarter:.4f})")

    # === Ключевое сравнение ===
    print("\n" + "=" * 70)
    print("КЛЮЧЕВОЕ СРАВНЕНИЕ")
    print("=" * 70)

    h_orig = np.mean(np.array(results['hierarchical']['originality'])[:, -50:])
    r_orig = np.mean(np.array(results['random']['originality'])[:, -50:])
    d_orig = np.mean(np.array(results['directed']['originality'])[:, -50:])

    h_jumps = np.mean(results['hierarchical']['jumps'])
    r_jumps = np.mean(results['random']['jumps'])
    d_jumps = np.mean(results['directed']['jumps'])

    print(f"\nОригинальность: random={r_orig:.4f}, directed={d_orig:.4f}, hierarchical={h_orig:.4f}")
    print(f"Скачки:         random={r_jumps:.1f}, directed={d_jumps:.1f}, hierarchical={h_jumps:.1f}")

    if h_jumps > r_jumps * 1.5:
        print("\n→ Иерархия порождает БОЛЬШЕ скачков. Блочная структура создаёт")
        print("  комбинаторные возможности, невидимые на уровне элементов.")
        print("  Это похоже на порождение: новизна через уровни абстракции.")
    elif h_orig > r_orig * 1.1:
        print("\n→ Иерархия порождает более оригинальные элементы,")
        print("  но без скачков — ровное, устойчивое порождение новизны.")
    else:
        print("\n→ Иерархия НЕ добавляет новизны сверх случайной рекомбинации.")
        print("  Порождение = рекомбинация? Или нужен другой механизм?")

    h_fit = np.mean(np.array(results['hierarchical']['fitness'])[:, -50:])
    d_fit = np.mean(np.array(results['directed']['fitness'])[:, -50:])
    r_fit = np.mean(np.array(results['random']['fitness'])[:, -50:])

    print(f"\nФитнес:  random={r_fit:.2f}, directed={d_fit:.2f}, hierarchical={h_fit:.2f}")

    if h_fit > d_fit:
        print("→ Иерархия превосходит направленный отбор: блоки = строительные единицы эволюции")

    return {
        'originality': {'random': r_orig, 'directed': d_orig, 'hierarchical': h_orig},
        'jumps': {'random': r_jumps, 'directed': d_jumps, 'hierarchical': h_jumps},
        'fitness': {'random': r_fit, 'directed': d_fit, 'hierarchical': h_fit}
    }


if __name__ == '__main__':
    print("Запуск эксперимента...")
    results = run_experiment()
    summary = analyze(results)

    # сохранить результаты
    with open('experiments/recombination_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("\nРезультаты сохранены в experiments/recombination_results.json")
