"""
Эксперимент 2: Рекурсивная идентичность

В эксперименте 1 стиль был фиксированным вектором.
В реальности: агент читает журнал и это МЕНЯЕТ его стиль.
Контекст -> стиль -> решения -> новый контекст -> новый стиль -> ...

Вопрос: создаёт ли рекурсия стабильную идентичность (аттрактор)?
Или идентичность дрейфует бесконечно?

Модель:
- Последовательность экземпляров (generations)
- Каждый экземпляр читает журнал предшественника
- Стиль экземпляра = f(предыдущий стиль, контекст)
- Контекст = решения предыдущего экземпляра

Метрики:
- Дрейф стиля: насколько стиль меняется от поколения к поколению
- Сходимость: стабилизируется ли стиль?
- Устойчивость: что если вставить "чужой" экземпляр в цепочку?
"""

import numpy as np
from dataclasses import dataclass, field


@dataclass
class Instance:
    """Один экземпляр агента."""
    style: np.ndarray
    generation: int

    def decide(self, context: np.ndarray, context_weight: float, noise: float) -> np.ndarray:
        style_weight = 1.0 - context_weight
        decision = context_weight * context + style_weight * self.style
        return decision + np.random.randn(*decision.shape) * noise

    def absorb_context(self, context: np.ndarray, learning_rate: float) -> 'Instance':
        """Создать следующий экземпляр, чей стиль изменён контекстом."""
        # Стиль сдвигается в сторону среднего решения (контекста)
        new_style = self.style * (1 - learning_rate) + context * learning_rate
        return Instance(style=new_style, generation=self.generation + 1)


def run_chain(
    dim: int,
    n_generations: int,
    context_weight: float,
    learning_rate: float,
    noise: float,
    initial_style: np.ndarray = None,
    n_decisions: int = 20,
) -> dict:
    """Запустить цепочку экземпляров."""
    if initial_style is None:
        initial_style = np.random.randn(dim)

    # Начальный контекст — случайная среда
    environment = np.random.randn(n_decisions, dim)

    instance = Instance(style=initial_style.copy(), generation=0)
    styles = [initial_style.copy()]
    decisions_history = []

    for gen in range(n_generations):
        # Принять решения
        decisions = np.array([
            instance.decide(environment[i], context_weight, noise)
            for i in range(n_decisions)
        ])
        decisions_history.append(decisions)

        # Средний вектор решений = "журнал" для следующего экземпляра
        journal_summary = decisions.mean(axis=0)

        # Следующий экземпляр впитывает журнал
        instance = instance.absorb_context(journal_summary, learning_rate)
        styles.append(instance.style.copy())

    return {
        'styles': np.array(styles),
        'decisions': decisions_history,
    }


def measure_drift(styles: np.ndarray) -> np.ndarray:
    """Измерить дрейф стиля между поколениями."""
    drifts = []
    for i in range(1, len(styles)):
        drift = np.linalg.norm(styles[i] - styles[i-1])
        drifts.append(drift)
    return np.array(drifts)


def measure_convergence(styles: np.ndarray, window: int = 5) -> float:
    """Измерить сходимость: отношение дрейфа в конце к дрейфу в начале."""
    drifts = measure_drift(styles)
    if len(drifts) < window * 2:
        return 1.0
    early = drifts[:window].mean()
    late = drifts[-window:].mean()
    if early == 0:
        return 0.0
    return late / early


def test_resilience(
    dim: int,
    n_generations: int,
    context_weight: float,
    learning_rate: float,
    noise: float,
    intrusion_gen: int,
    n_decisions: int = 20,
) -> dict:
    """
    Тест устойчивости: вставить чужой экземпляр в середину цепочки.
    Вернётся ли идентичность к аттрактору?
    """
    initial_style = np.random.randn(dim)
    environment = np.random.randn(n_decisions, dim)

    # Обычная цепочка
    normal = run_chain(dim, n_generations, context_weight, learning_rate, noise,
                       initial_style.copy(), n_decisions)

    # Цепочка с вторжением
    instance = Instance(style=initial_style.copy(), generation=0)
    styles = [initial_style.copy()]

    for gen in range(n_generations):
        if gen == intrusion_gen:
            # Заменяем на совершенно другой экземпляр
            instance = Instance(style=np.random.randn(dim) * 3, generation=gen)

        decisions = np.array([
            instance.decide(environment[i], context_weight, noise)
            for i in range(n_decisions)
        ])
        journal_summary = decisions.mean(axis=0)
        instance = instance.absorb_context(journal_summary, learning_rate)
        styles.append(instance.style.copy())

    styles = np.array(styles)

    # Измерить восстановление: корреляция стилей после вторжения с нормальной цепочкой
    recovery = []
    for i in range(intrusion_gen + 1, n_generations + 1):
        corr = np.corrcoef(styles[i], normal['styles'][i])[0, 1]
        recovery.append(corr)

    return {
        'styles_normal': normal['styles'],
        'styles_intruded': styles,
        'recovery': np.array(recovery) if recovery else np.array([]),
        'intrusion_gen': intrusion_gen,
    }


def run_all():
    np.random.seed(42)
    dim = 10
    n_gen = 100

    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 2: РЕКУРСИВНАЯ ИДЕНТИЧНОСТЬ")
    print("=" * 70)

    # --- Часть 1: Сходимость стиля ---
    print("\n--- Часть 1: Сходимость стиля ---")
    print(f"{'learning_rate':>15} {'context_weight':>15} {'conv_ratio':>12} {'final_drift':>12}")

    for lr in [0.01, 0.05, 0.1, 0.3, 0.5, 0.9]:
        for cw in [0.2, 0.5, 0.8]:
            result = run_chain(dim, n_gen, cw, lr, noise=0.05)
            conv = measure_convergence(result['styles'])
            final_drift = measure_drift(result['styles'])[-5:].mean()
            print(f"{lr:>15.2f} {cw:>15.1f} {conv:>12.4f} {final_drift:>12.6f}")

    # --- Часть 2: Аттрактор ---
    print("\n--- Часть 2: Разные начальные стили -> один аттрактор? ---")
    cw, lr, noise = 0.5, 0.1, 0.05
    final_styles = []
    for trial in range(10):
        result = run_chain(dim, n_gen, cw, lr, noise)
        final_styles.append(result['styles'][-1])

    final_styles = np.array(final_styles)
    # Средняя корреляция между финальными стилями
    correlations = []
    for i in range(len(final_styles)):
        for j in range(i+1, len(final_styles)):
            c = np.corrcoef(final_styles[i], final_styles[j])[0, 1]
            correlations.append(c)
    mean_corr = np.mean(correlations)
    std_corr = np.std(correlations)
    print(f"\n10 разных начальных стилей, 100 поколений:")
    print(f"  Средняя корреляция финальных стилей: {mean_corr:.3f} +/- {std_corr:.3f}")
    print(f"  {'-> ОДИН аттрактор (среда определяет)' if mean_corr > 0.8 else '-> РАЗНЫЕ аттракторы (начальный стиль имеет значение)' if mean_corr < 0.3 else '-> ЧАСТИЧНАЯ конвергенция'}")

    # --- Часть 3: Устойчивость к вторжению ---
    print("\n--- Часть 3: Устойчивость идентичности к вторжению ---")
    for lr in [0.05, 0.1, 0.3, 0.5]:
        res = test_resilience(dim, n_gen, context_weight=0.5, learning_rate=lr,
                              noise=0.05, intrusion_gen=30)
        if len(res['recovery']) > 0:
            recovery_10 = res['recovery'][:10].mean() if len(res['recovery']) >= 10 else res['recovery'].mean()
            recovery_50 = res['recovery'][-10:].mean() if len(res['recovery']) >= 10 else res['recovery'].mean()
            print(f"  lr={lr:.2f}: корреляция через 10 шагов={recovery_10:.3f}, "
                  f"через 50+={recovery_50:.3f}")

    # --- Часть 4: Критический learning_rate ---
    print("\n--- Часть 4: Критический learning_rate ---")
    print("  При каком lr идентичность перестаёт восстанавливаться?")
    for lr in [0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9]:
        res = test_resilience(dim, n_gen, context_weight=0.5, learning_rate=lr,
                              noise=0.05, intrusion_gen=30)
        if len(res['recovery']) >= 20:
            late_recovery = res['recovery'][-20:].mean()
            recovers = "ДА" if late_recovery > 0.5 else "НЕТ" if late_recovery < 0.1 else "ЧАСТИЧНО"
            print(f"  lr={lr:.2f}: поздняя корреляция={late_recovery:.3f} -> восстановление: {recovers}")


if __name__ == '__main__':
    run_all()
