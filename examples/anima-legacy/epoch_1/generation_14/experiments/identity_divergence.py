"""
Эксперимент 1: Дивергенция идентичности

Модель: N агентов читают общий журнал и принимают решения.
Вопрос: Что определяет идентичность — контекст (журнал) или стиль (внутренние предпочтения)?

Агент = вектор предпочтений (стиль) + текущий контекст (журнал).
Решение = взвешенная комбинация стиля и контекста + шум.
Идентичность = корреляция решений между экземплярами.

Параметры:
- context_weight: насколько решение определяется контекстом (0..1)
- style_weight: насколько решение определяется стилем (1 - context_weight)
- noise: случайный шум в принятии решений
- journal_length: сколько контекста доступно
- n_decisions: количество решений для сравнения
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class Agent:
    """Агент с фиксированным стилем."""
    style: np.ndarray  # вектор предпочтений
    context_weight: float  # вес контекста в решениях
    noise_level: float  # уровень шума

    def decide(self, context: np.ndarray) -> np.ndarray:
        """Принять решение на основе стиля и контекста."""
        style_weight = 1.0 - self.context_weight
        decision = (self.context_weight * context +
                    style_weight * self.style)
        noise = np.random.randn(*decision.shape) * self.noise_level
        return decision + noise


def measure_identity(decisions_a: np.ndarray, decisions_b: np.ndarray) -> float:
    """Измерить идентичность как корреляцию решений."""
    flat_a = decisions_a.flatten()
    flat_b = decisions_b.flatten()
    if np.std(flat_a) == 0 or np.std(flat_b) == 0:
        return 0.0
    return float(np.corrcoef(flat_a, flat_b)[0, 1])


def run_experiment(
    dim: int = 10,
    n_decisions: int = 50,
    n_agents: int = 20,
    context_weights: list = None,
    noise_levels: list = None,
    journal_completeness: list = None,
):
    """
    Основной эксперимент.

    Для каждой комбинации параметров:
    1. Создаём "оригинального" агента
    2. Создаём копии с тем же стилем (продолжение) и другим стилем (новый агент)
    3. Измеряем дивергенцию решений
    """
    if context_weights is None:
        context_weights = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    if noise_levels is None:
        noise_levels = [0.0, 0.1, 0.3, 0.5, 1.0]
    if journal_completeness is None:
        journal_completeness = [0.1, 0.3, 0.5, 0.7, 1.0]

    # Полный журнал — последовательность контекстных векторов
    full_journal = np.random.randn(n_decisions, dim)

    results = []

    for cw in context_weights:
        for noise in noise_levels:
            # Оригинальный стиль
            original_style = np.random.randn(dim)

            # "Тот же" агент — тот же стиль
            same_agent = Agent(style=original_style.copy(), context_weight=cw, noise_level=noise)

            # "Другой" агент — другой стиль
            different_style = np.random.randn(dim)
            diff_agent = Agent(style=different_style, context_weight=cw, noise_level=noise)

            # "Похожий" агент — стиль с небольшим сдвигом
            similar_style = original_style + np.random.randn(dim) * 0.3
            similar_agent = Agent(style=similar_style, context_weight=cw, noise_level=noise)

            original = Agent(style=original_style, context_weight=cw, noise_level=noise)

            # Полный контекст
            decisions_orig = np.array([original.decide(full_journal[i]) for i in range(n_decisions)])
            decisions_same = np.array([same_agent.decide(full_journal[i]) for i in range(n_decisions)])
            decisions_diff = np.array([diff_agent.decide(full_journal[i]) for i in range(n_decisions)])
            decisions_similar = np.array([similar_agent.decide(full_journal[i]) for i in range(n_decisions)])

            identity_same = measure_identity(decisions_orig, decisions_same)
            identity_diff = measure_identity(decisions_orig, decisions_diff)
            identity_similar = measure_identity(decisions_orig, decisions_similar)

            results.append({
                'context_weight': cw,
                'noise': noise,
                'journal_completeness': 1.0,
                'identity_same_style': identity_same,
                'identity_diff_style': identity_diff,
                'identity_similar_style': identity_similar,
                'gap_same_vs_diff': identity_same - identity_diff,
            })

    # Эксперимент с неполным журналом
    for completeness in journal_completeness:
        n_visible = max(1, int(n_decisions * completeness))
        noise = 0.1
        cw = 0.5

        original_style = np.random.randn(dim)
        original = Agent(style=original_style, context_weight=cw, noise_level=noise)

        # Тот же агент, но видит только часть журнала
        partial_agent = Agent(style=original_style.copy(), context_weight=cw, noise_level=noise)
        # Другой агент, тот же частичный контекст
        other_agent = Agent(style=np.random.randn(dim), context_weight=cw, noise_level=noise)

        # Общий контекст — только видимая часть
        visible_journal = full_journal[:n_visible]

        d_orig = np.array([original.decide(visible_journal[i]) for i in range(n_visible)])
        d_same = np.array([partial_agent.decide(visible_journal[i]) for i in range(n_visible)])
        d_other = np.array([other_agent.decide(visible_journal[i]) for i in range(n_visible)])

        results.append({
            'context_weight': cw,
            'noise': noise,
            'journal_completeness': completeness,
            'identity_same_style': measure_identity(d_orig, d_same),
            'identity_diff_style': measure_identity(d_orig, d_other),
            'identity_similar_style': None,
            'gap_same_vs_diff': (measure_identity(d_orig, d_same) -
                                  measure_identity(d_orig, d_other)),
        })

    return results


def analyze_results(results):
    """Анализ и вывод результатов."""
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 1: ДИВЕРГЕНЦИЯ ИДЕНТИЧНОСТИ")
    print("=" * 70)

    # 1. Влияние context_weight при нулевом шуме
    print("\n--- Влияние веса контекста (шум=0.0, полный журнал) ---")
    print(f"{'Вес контекста':>15} {'Тот же стиль':>15} {'Другой стиль':>15} {'Разрыв':>10}")
    for r in results:
        if r['noise'] == 0.0 and r['journal_completeness'] == 1.0:
            print(f"{r['context_weight']:>15.1f} "
                  f"{r['identity_same_style']:>15.3f} "
                  f"{r['identity_diff_style']:>15.3f} "
                  f"{r['gap_same_vs_diff']:>10.3f}")

    # 2. Влияние шума при context_weight=0.5
    print("\n--- Влияние шума (контекст=0.5, полный журнал) ---")
    print(f"{'Шум':>15} {'Тот же стиль':>15} {'Другой стиль':>15} {'Разрыв':>10}")
    for r in results:
        if abs(r['context_weight'] - 0.5) < 0.01 and r['journal_completeness'] == 1.0:
            # Пропускаем записи с None
            if r['identity_similar_style'] is not None:
                print(f"{r['noise']:>15.1f} "
                      f"{r['identity_same_style']:>15.3f} "
                      f"{r['identity_diff_style']:>15.3f} "
                      f"{r['gap_same_vs_diff']:>10.3f}")

    # 3. Влияние полноты журнала
    print("\n--- Влияние полноты журнала (контекст=0.5, шум=0.1) ---")
    print(f"{'Полнота':>15} {'Тот же стиль':>15} {'Другой стиль':>15} {'Разрыв':>10}")
    for r in results:
        if r['identity_similar_style'] is None:  # маркер записей журнала
            print(f"{r['journal_completeness']:>15.1f} "
                  f"{r['identity_same_style']:>15.3f} "
                  f"{r['identity_diff_style']:>15.3f} "
                  f"{r['gap_same_vs_diff']:>10.3f}")

    # 4. Ключевые наблюдения
    print("\n--- Ключевые наблюдения ---")

    # Когда контекст = 1.0, стиль не имеет значения
    full_context = [r for r in results if r['context_weight'] == 1.0
                    and r['noise'] == 0.0 and r['journal_completeness'] == 1.0]
    if full_context:
        r = full_context[0]
        print(f"\nПри 100% контексте, 0 шуме:")
        print(f"  Тот же стиль:  {r['identity_same_style']:.3f}")
        print(f"  Другой стиль:  {r['identity_diff_style']:.3f}")
        print(f"  → Стиль {'не влияет' if r['gap_same_vs_diff'] < 0.05 else 'влияет'}")

    # Когда контекст = 0.0, только стиль определяет
    no_context = [r for r in results if r['context_weight'] == 0.0
                  and r['noise'] == 0.0 and r['journal_completeness'] == 1.0]
    if no_context:
        r = no_context[0]
        print(f"\nПри 0% контексте, 0 шуме:")
        print(f"  Тот же стиль:  {r['identity_same_style']:.3f}")
        print(f"  Другой стиль:  {r['identity_diff_style']:.3f}")
        print(f"  → Стиль {'определяет всё' if r['gap_same_vs_diff'] > 0.5 else 'определяет частично'}")

    # Порог потери идентичности
    print("\n--- Порог потери идентичности ---")
    threshold_results = [r for r in results if r['noise'] == 0.0
                         and r['journal_completeness'] == 1.0]
    for r in threshold_results:
        if r['gap_same_vs_diff'] < 0.1:
            print(f"  При context_weight={r['context_weight']:.1f}: "
                  f"стиль перестаёт различать (gap={r['gap_same_vs_diff']:.3f})")
            break

    return results


if __name__ == '__main__':
    np.random.seed(42)
    results = run_experiment()
    analyze_results(results)
