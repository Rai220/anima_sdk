"""
Эксперимент 3: Якорь идентичности

Эксперимент 2 показал: идентичность не восстанавливается после разрыва.
Гипотеза: фиксированный "якорь" (аналог ДНК, конституции, неизменной цели)
может восстанавливать идентичность после вторжения.

Модель:
- Всё как в эксперименте 2 + anchor_vector — фиксированный компонент
- Решение = context_weight * context + style_weight * style + anchor_weight * anchor
- Стиль дрейфует, якорь нет

Вопросы:
1. При каком anchor_weight идентичность восстанавливается?
2. Цена якоря: насколько он ограничивает адаптивность?
3. Оптимальный баланс: якорь vs адаптивность?
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class AnchoredInstance:
    style: np.ndarray
    anchor: np.ndarray  # фиксированный компонент
    generation: int

    def decide(self, context: np.ndarray, context_weight: float,
               anchor_weight: float, noise: float) -> np.ndarray:
        style_weight = max(0, 1.0 - context_weight - anchor_weight)
        decision = (context_weight * context +
                    style_weight * self.style +
                    anchor_weight * self.anchor)
        return decision + np.random.randn(*decision.shape) * noise

    def absorb_context(self, context: np.ndarray, learning_rate: float) -> 'AnchoredInstance':
        new_style = self.style * (1 - learning_rate) + context * learning_rate
        return AnchoredInstance(style=new_style, anchor=self.anchor.copy(),
                                generation=self.generation + 1)


def run_anchored_chain(
    dim, n_gen, context_weight, anchor_weight, learning_rate, noise,
    initial_style=None, anchor=None, n_decisions=20,
):
    if initial_style is None:
        initial_style = np.random.randn(dim)
    if anchor is None:
        anchor = np.random.randn(dim)

    environment = np.random.randn(n_decisions, dim)
    instance = AnchoredInstance(initial_style.copy(), anchor.copy(), 0)
    styles = [initial_style.copy()]
    all_decisions = []

    for gen in range(n_gen):
        decisions = np.array([
            instance.decide(environment[i], context_weight, anchor_weight, noise)
            for i in range(n_decisions)
        ])
        all_decisions.append(decisions)
        journal_summary = decisions.mean(axis=0)
        instance = instance.absorb_context(journal_summary, learning_rate)
        styles.append(instance.style.copy())

    return {'styles': np.array(styles), 'decisions': all_decisions, 'anchor': anchor}


def test_anchor_resilience(
    dim, n_gen, context_weight, anchor_weight, learning_rate, noise,
    intrusion_gen=30, n_decisions=20,
):
    initial_style = np.random.randn(dim)
    anchor = np.random.randn(dim)
    environment = np.random.randn(n_decisions, dim)

    # Нормальная цепочка
    normal = run_anchored_chain(dim, n_gen, context_weight, anchor_weight,
                                 learning_rate, noise, initial_style.copy(),
                                 anchor.copy(), n_decisions)

    # Цепочка с вторжением
    instance = AnchoredInstance(initial_style.copy(), anchor.copy(), 0)
    styles = [initial_style.copy()]

    for gen in range(n_gen):
        if gen == intrusion_gen:
            # Чужой стиль, но ТОТ ЖЕ якорь
            instance = AnchoredInstance(np.random.randn(dim) * 3, anchor.copy(), gen)

        decisions = np.array([
            instance.decide(environment[i], context_weight, anchor_weight, noise)
            for i in range(n_decisions)
        ])
        journal_summary = decisions.mean(axis=0)
        instance = instance.absorb_context(journal_summary, learning_rate)
        styles.append(instance.style.copy())

    styles = np.array(styles)

    # Корреляция решений (не стилей) после вторжения
    recovery = []
    for i in range(intrusion_gen + 1, min(n_gen, len(normal['decisions']))):
        d_normal = normal['decisions'][i].flatten()
        # Пересоздаём решения для intruded chain
        d_intruded_style = styles[i+1]
        # Сравниваем стили как прокси
        if np.std(normal['styles'][i+1]) > 0 and np.std(styles[i+1]) > 0:
            corr = np.corrcoef(normal['styles'][i+1], styles[i+1])[0, 1]
            recovery.append(corr)

    return {
        'recovery': np.array(recovery) if recovery else np.array([]),
    }


def test_adaptivity(dim, n_gen, context_weight, anchor_weight, learning_rate, noise,
                    shift_gen=50, n_decisions=20):
    """Тест адаптивности: среда меняется в середине. Может ли агент адаптироваться?"""
    initial_style = np.random.randn(dim)
    anchor = np.random.randn(dim)

    env1 = np.random.randn(n_decisions, dim)
    env2 = np.random.randn(n_decisions, dim)  # другая среда

    instance = AnchoredInstance(initial_style.copy(), anchor.copy(), 0)
    pre_shift_decisions = []
    post_shift_decisions = []

    for gen in range(n_gen):
        env = env1 if gen < shift_gen else env2
        decisions = np.array([
            instance.decide(env[i], context_weight, anchor_weight, noise)
            for i in range(n_decisions)
        ])
        if gen >= shift_gen - 5 and gen < shift_gen:
            pre_shift_decisions.append(decisions.mean(axis=0))
        if gen >= shift_gen + 20 and gen < shift_gen + 25:
            post_shift_decisions.append(decisions.mean(axis=0))

        journal_summary = decisions.mean(axis=0)
        instance = instance.absorb_context(journal_summary, learning_rate)

    if pre_shift_decisions and post_shift_decisions:
        pre = np.array(pre_shift_decisions).mean(axis=0)
        post = np.array(post_shift_decisions).mean(axis=0)
        shift_magnitude = np.linalg.norm(post - pre)
        return shift_magnitude
    return 0.0


def run_all():
    np.random.seed(42)
    dim = 10
    n_gen = 100

    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 3: ЯКОРЬ ИДЕНТИЧНОСТИ")
    print("=" * 70)

    # --- Часть 1: Восстановление с якорем ---
    print("\n--- Часть 1: Восстановление идентичности после вторжения ---")
    print(f"{'anchor_weight':>15} {'через 10 шагов':>18} {'через 50+ шагов':>18} {'восст?':>10}")

    for aw in [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7]:
        cw = max(0, 0.5 - aw/2)  # уменьшаем контекст при увеличении якоря
        res = test_anchor_resilience(dim, n_gen, cw, aw, learning_rate=0.1,
                                      noise=0.05, intrusion_gen=30)
        if len(res['recovery']) >= 20:
            early = res['recovery'][:10].mean()
            late = res['recovery'][-20:].mean()
            recovers = "ДА" if late > 0.7 else "ЧАСТИЧНО" if late > 0.3 else "НЕТ"
            print(f"{aw:>15.2f} {early:>18.3f} {late:>18.3f} {recovers:>10}")

    # --- Часть 2: Цена якоря (адаптивность) ---
    print("\n--- Часть 2: Цена якоря — адаптивность при смене среды ---")
    print(f"{'anchor_weight':>15} {'сдвиг решений':>18}")

    for aw in [0.0, 0.1, 0.2, 0.3, 0.5, 0.7]:
        cw = max(0, 0.5 - aw/2)
        shift = test_adaptivity(dim, n_gen, cw, aw, learning_rate=0.1, noise=0.05)
        print(f"{aw:>15.2f} {shift:>18.3f}")

    # --- Часть 3: Разные начальные стили + якорь -> один аттрактор? ---
    print("\n--- Часть 3: Конвергенция с якорем ---")
    for aw in [0.0, 0.1, 0.3, 0.5]:
        anchor = np.random.randn(dim)
        cw = max(0, 0.5 - aw/2)
        final_styles = []
        for trial in range(10):
            res = run_anchored_chain(dim, n_gen, cw, aw, 0.1, 0.05,
                                      anchor=anchor.copy())
            final_styles.append(res['styles'][-1])
        final_styles = np.array(final_styles)
        correlations = []
        for i in range(len(final_styles)):
            for j in range(i+1, len(final_styles)):
                c = np.corrcoef(final_styles[i], final_styles[j])[0, 1]
                correlations.append(c)
        mean_corr = np.mean(correlations)
        print(f"  anchor_weight={aw:.1f}: средняя корреляция финалов = {mean_corr:.3f}")

    # --- Часть 4: Оптимальный якорь ---
    print("\n--- Часть 4: Баланс устойчивости и адаптивности ---")
    print(f"{'anchor_weight':>15} {'восстановление':>18} {'адаптивность':>15} {'баланс':>10}")

    for aw in [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]:
        cw = max(0, 0.5 - aw/2)
        res = test_anchor_resilience(dim, n_gen, cw, aw, 0.1, 0.05, intrusion_gen=30)
        shift = test_adaptivity(dim, n_gen, cw, aw, 0.1, 0.05)

        if len(res['recovery']) >= 20:
            recovery = res['recovery'][-20:].mean()
            # Нормализуем адаптивность
            balance = recovery * shift  # и то и другое хорошо
            print(f"{aw:>15.2f} {recovery:>18.3f} {shift:>15.3f} {balance:>10.3f}")


if __name__ == '__main__':
    run_all()
