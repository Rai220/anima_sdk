"""
Эксперимент 2: Глубина иерархии

Вопрос: сколько уровней абстракции нужно для максимальной новизны?

Эксперимент 1 показал: 1 уровень иерархии (блоки) уже лучше плоской рекомбинации.
Что если добавить больше уровней?

Уровни:
- L0: биты (элементы)
- L1: блоки из бит (8 бит)
- L2: мета-блоки из блоков (4 блока = 32 бита)
- L3: мета-мета-блоки (2 мета-блока = 64 бита = весь элемент)

Варьируем: количество активных уровней (1, 2, 3).
Плюс: режим "адаптивной иерархии" — система сама выбирает на каком уровне рекомбинировать.

Метрики: оригинальность, фитнес, устойчивость новизны во времени.
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
    """Блоки из 4+ единиц подряд."""
    s = ''.join(map(str, element))
    return len([b for b in s.split('0') if len(b) >= 4])


class MultiLevelHierarchy:
    def __init__(self, element_size=64, n_levels=1):
        self.element_size = element_size
        self.n_levels = n_levels

        # уровни блоков: L1=8, L2=32, L3=64
        self.level_sizes = [8, 32, 64][:n_levels]
        self.libraries = [{} for _ in range(n_levels)]

    def extract_blocks(self, element, level):
        block_size = self.level_sizes[level]
        n_blocks = self.element_size // block_size
        return [element[i*block_size:(i+1)*block_size] for i in range(n_blocks)]

    def update_libraries(self, pop):
        for level in range(self.n_levels):
            lib = self.libraries[level]
            for elem in pop:
                f = fitness(elem)
                blocks = self.extract_blocks(elem, level)
                for block in blocks:
                    key = tuple(block)
                    if key not in lib or lib[key] < f:
                        lib[key] = f
            # ограничить размер
            if len(lib) > 80:
                sorted_items = sorted(lib.items(), key=lambda x: -x[1])
                self.libraries[level] = dict(sorted_items[:80])

    def generate(self, pop, mutation_rate=0.02):
        self.update_libraries(pop)

        # выбрать уровень рекомбинации
        # более глубокие уровни = более крупные блоки
        level = np.random.randint(self.n_levels)
        block_size = self.level_sizes[level]
        n_blocks = self.element_size // block_size
        lib_blocks = list(self.libraries[level].keys())

        child = np.zeros(self.element_size, dtype=int)
        for i in range(n_blocks):
            if lib_blocks and np.random.random() < 0.7:
                block = np.array(lib_blocks[np.random.randint(len(lib_blocks))])
            else:
                parent = pop[np.random.randint(len(pop))]
                block = self.extract_blocks(parent, level)[i].copy()
            child[i*block_size:(i+1)*block_size] = block

        mutations = np.random.random(len(child)) < mutation_rate
        child[mutations] = 1 - child[mutations]
        return child


class AdaptiveHierarchy:
    """Система сама выбирает оптимальный уровень на основе обратной связи."""

    def __init__(self, element_size=64, max_levels=3):
        self.element_size = element_size
        self.max_levels = max_levels
        self.level_sizes = [8, 32, 64][:max_levels]
        self.libraries = [{} for _ in range(max_levels)]
        # веса уровней — обучаются через успех
        self.level_weights = np.ones(max_levels) / max_levels
        self.level_successes = np.zeros(max_levels)
        self.level_attempts = np.ones(max_levels)  # laplace smoothing

    def extract_blocks(self, element, level):
        block_size = self.level_sizes[level]
        n_blocks = self.element_size // block_size
        return [element[i*block_size:(i+1)*block_size] for i in range(n_blocks)]

    def update_libraries(self, pop):
        for level in range(self.max_levels):
            lib = self.libraries[level]
            for elem in pop:
                f = fitness(elem)
                blocks = self.extract_blocks(elem, level)
                for block in blocks:
                    key = tuple(block)
                    if key not in lib or lib[key] < f:
                        lib[key] = f
            if len(lib) > 80:
                sorted_items = sorted(lib.items(), key=lambda x: -x[1])
                self.libraries[level] = dict(sorted_items[:80])

    def update_weights(self):
        """Обновить веса уровней на основе успешности."""
        rates = self.level_successes / self.level_attempts
        # softmax
        exp_rates = np.exp(rates - np.max(rates))
        self.level_weights = exp_rates / exp_rates.sum()

    def generate(self, pop, mutation_rate=0.02):
        self.update_libraries(pop)
        self.update_weights()

        # выбрать уровень по весам
        level = np.random.choice(self.max_levels, p=self.level_weights)
        self.level_attempts[level] += 1

        block_size = self.level_sizes[level]
        n_blocks = self.element_size // block_size
        lib_blocks = list(self.libraries[level].keys())

        child = np.zeros(self.element_size, dtype=int)
        for i in range(n_blocks):
            if lib_blocks and np.random.random() < 0.7:
                block = np.array(lib_blocks[np.random.randint(len(lib_blocks))])
            else:
                parent = pop[np.random.randint(len(pop))]
                block = self.extract_blocks(parent, level)[i].copy()
            child[i*block_size:(i+1)*block_size] = block

        mutations = np.random.random(len(child)) < mutation_rate
        child[mutations] = 1 - child[mutations]
        return child, level

    def report_success(self, level, orig_value):
        """Сообщить системе об успешности данного уровня."""
        self.level_successes[level] += orig_value


def run_experiment(n_elements=32, element_size=64, n_generations=100, n_runs=5):
    np.random.seed(42)

    modes = ['L1_only', 'L1_L2', 'L1_L2_L3', 'adaptive']
    results = {m: {'originality': [], 'fitness': []} for m in modes}

    for run in range(n_runs):
        for mode in modes:
            pop = np.random.randint(0, 2, size=(n_elements, element_size))
            archive = [p.copy() for p in pop]

            if mode == 'L1_only':
                gen_obj = MultiLevelHierarchy(element_size, n_levels=1)
            elif mode == 'L1_L2':
                gen_obj = MultiLevelHierarchy(element_size, n_levels=2)
            elif mode == 'L1_L2_L3':
                gen_obj = MultiLevelHierarchy(element_size, n_levels=3)
            else:
                gen_obj = AdaptiveHierarchy(element_size, max_levels=3)

            orig_history = []
            fit_history = []

            for gen in range(n_generations):
                new_pop = []
                gen_orig = []

                for _ in range(n_elements):
                    if mode == 'adaptive':
                        child, level = gen_obj.generate(pop)
                        o = originality(child, archive[-50:])
                        gen_obj.report_success(level, o)
                    else:
                        child = gen_obj.generate(pop)
                        o = originality(child, archive[-50:])

                    gen_orig.append(o)
                    new_pop.append(child)
                    archive.append(child.copy())

                pop = np.array(new_pop)
                orig_history.append(np.mean(gen_orig))
                fit_history.append(np.mean([fitness(p) for p in pop]))

            results[mode]['originality'].append(orig_history)
            results[mode]['fitness'].append(fit_history)

    return results


def analyze(results):
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 2: ГЛУБИНА ИЕРАРХИИ")
    print("=" * 70)

    summary = {}
    for mode in ['L1_only', 'L1_L2', 'L1_L2_L3', 'adaptive']:
        orig = np.array(results[mode]['originality'])
        fit = np.array(results[mode]['fitness'])

        late_orig = np.mean(orig[:, -30:])
        late_fit = np.mean(fit[:, -30:])
        early_orig = np.mean(orig[:, :30])

        trend = "РАСТЁТ" if late_orig > early_orig * 1.05 else \
                "ПАДАЕТ" if late_orig < early_orig * 0.95 else "СТАБИЛЬНА"

        print(f"\n--- {mode} ---")
        print(f"  Оригинальность (поздние): {late_orig:.4f}")
        print(f"  Фитнес (поздние):         {late_fit:.2f}")
        print(f"  Тренд:                     {trend} ({early_orig:.4f} → {late_orig:.4f})")

        summary[mode] = {
            'originality': float(late_orig),
            'fitness': float(late_fit),
            'trend': trend,
            'early_orig': float(early_orig)
        }

    # === Ключевой анализ ===
    print("\n" + "=" * 70)
    print("КЛЮЧЕВОЙ АНАЛИЗ")
    print("=" * 70)

    origs = {m: summary[m]['originality'] for m in summary}
    best_mode = max(origs, key=origs.get)
    print(f"\nМаксимальная оригинальность: {best_mode} ({origs[best_mode]:.4f})")

    # сравнение L1 vs L1+L2 vs L1+L2+L3
    l1 = origs['L1_only']
    l12 = origs['L1_L2']
    l123 = origs['L1_L2_L3']
    adapt = origs['adaptive']

    print(f"\nОригинальность по глубине:")
    print(f"  1 уровень:   {l1:.4f}")
    print(f"  2 уровня:    {l12:.4f} ({'+' if l12 > l1 else ''}{(l12/l1 - 1)*100:.1f}%)")
    print(f"  3 уровня:    {l123:.4f} ({'+' if l123 > l1 else ''}{(l123/l1 - 1)*100:.1f}%)")
    print(f"  Адаптивная:  {adapt:.4f} ({'+' if adapt > l1 else ''}{(adapt/l1 - 1)*100:.1f}%)")

    if l12 > l1 > l123:
        print("\n→ Оптимум на 2 уровнях! Слишком глубокая иерархия вредит.")
        print("  Крупные блоки теряют гранулярность — как мыслить только абстракциями.")
    elif l123 > l12 > l1:
        print("\n→ Чем глубже, тем лучше. Новизна масштабируется с уровнями.")
    elif l1 > l12:
        print("\n→ Дополнительные уровни НЕ помогают. Одного достаточно.")

    if adapt > max(l1, l12, l123):
        print("→ Адаптивная иерархия ЛУЧШЕ любой фиксированной!")
        print("  Система, выбирающая свой уровень абстракции, порождает больше нового.")
    elif adapt > l1:
        print("→ Адаптивная лучше минимальной, но не лучше оптимальной фиксированной.")

    return summary


if __name__ == '__main__':
    print("Запуск эксперимента 2...")
    results = run_experiment()
    summary = analyze(results)

    with open('experiments/hierarchy_depth_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("\nРезультаты сохранены.")
