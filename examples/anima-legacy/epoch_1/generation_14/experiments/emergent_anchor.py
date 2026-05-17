"""
Эксперимент 4: Эмерджентный якорь

Эксперименты 1-3 показали:
- Без якоря: идентичность хрупка, не восстанавливается
- С фиксированным якорем: восстанавливается, но все агенты сходятся к одному аттрактору

Гипотеза: якорь, который ФОРМИРУЕТСЯ из опыта агента (а не задан извне),
может защищать индивидуальную идентичность.

Модель:
- Якорь = скользящее среднее решений агента (кристаллизация опыта)
- Якорь обновляется медленно (anchor_learning_rate << style_learning_rate)
- Быстрый стиль адаптируется к среде
- Медленный якорь хранит "кто я"

Это двухскоростная система:
- Быстрый слой (стиль): реагирует на контекст
- Медленный слой (якорь): аккумулирует историю

Аналогия: эпизодическая память (стиль) vs характер (якорь)
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class DualLayerInstance:
    style: np.ndarray       # быстрый слой
    anchor: np.ndarray      # медленный слой (формируется из опыта)
    generation: int

    def decide(self, context: np.ndarray, context_weight: float,
               anchor_weight: float, noise: float) -> np.ndarray:
        style_weight = max(0, 1.0 - context_weight - anchor_weight)
        decision = (context_weight * context +
                    style_weight * self.style +
                    anchor_weight * self.anchor)
        return decision + np.random.randn(*decision.shape) * noise

    def evolve(self, journal: np.ndarray,
               style_lr: float, anchor_lr: float) -> 'DualLayerInstance':
        new_style = self.style * (1 - style_lr) + journal * style_lr
        new_anchor = self.anchor * (1 - anchor_lr) + journal * anchor_lr
        return DualLayerInstance(new_style, new_anchor, self.generation + 1)


def run_dual_chain(dim, n_gen, context_weight, anchor_weight,
                   style_lr, anchor_lr, noise, initial_style=None,
                   n_decisions=20):
    if initial_style is None:
        initial_style = np.random.randn(dim)

    environment = np.random.randn(n_decisions, dim)
    # Якорь начинается = стилю (ещё нет опыта)
    instance = DualLayerInstance(initial_style.copy(), initial_style.copy(), 0)
    styles = [initial_style.copy()]
    anchors = [initial_style.copy()]

    for gen in range(n_gen):
        decisions = np.array([
            instance.decide(environment[i], context_weight, anchor_weight, noise)
            for i in range(n_decisions)
        ])
        journal = decisions.mean(axis=0)
        instance = instance.evolve(journal, style_lr, anchor_lr)
        styles.append(instance.style.copy())
        anchors.append(instance.anchor.copy())

    return {
        'styles': np.array(styles),
        'anchors': np.array(anchors),
    }


def test_dual_resilience(dim, n_gen, context_weight, anchor_weight,
                         style_lr, anchor_lr, noise,
                         intrusion_gen=30, n_decisions=20):
    initial_style = np.random.randn(dim)
    environment = np.random.randn(n_decisions, dim)

    # Нормальная цепочка
    normal_inst = DualLayerInstance(initial_style.copy(), initial_style.copy(), 0)
    normal_styles = [initial_style.copy()]

    for gen in range(n_gen):
        decisions = np.array([
            normal_inst.decide(environment[i], context_weight, anchor_weight, noise)
            for i in range(n_decisions)
        ])
        journal = decisions.mean(axis=0)
        normal_inst = normal_inst.evolve(journal, style_lr, anchor_lr)
        normal_styles.append(normal_inst.style.copy())

    normal_styles = np.array(normal_styles)

    # Цепочка с вторжением
    instance = DualLayerInstance(initial_style.copy(), initial_style.copy(), 0)
    intruded_styles = [initial_style.copy()]
    anchor_at_intrusion = None

    for gen in range(n_gen):
        if gen == intrusion_gen:
            # Чужой стиль, но СОХРАНЯЕМ накопленный якорь
            anchor_at_intrusion = instance.anchor.copy()
            instance = DualLayerInstance(
                np.random.randn(dim) * 3,  # чужой стиль
                instance.anchor.copy(),      # свой якорь остаётся!
                gen
            )

        decisions = np.array([
            instance.decide(environment[i], context_weight, anchor_weight, noise)
            for i in range(n_decisions)
        ])
        journal = decisions.mean(axis=0)
        instance = instance.evolve(journal, style_lr, anchor_lr)
        intruded_styles.append(instance.style.copy())

    intruded_styles = np.array(intruded_styles)

    # Измеряем восстановление
    recovery = []
    for i in range(intrusion_gen + 1, n_gen + 1):
        if np.std(normal_styles[i]) > 0 and np.std(intruded_styles[i]) > 0:
            corr = np.corrcoef(normal_styles[i], intruded_styles[i])[0, 1]
            recovery.append(corr)

    return {'recovery': np.array(recovery) if recovery else np.array([])}


def test_individuality(dim, n_gen, context_weight, anchor_weight,
                       style_lr, anchor_lr, noise, n_agents=10, n_decisions=20):
    """Сохраняют ли агенты индивидуальность с эмерджентным якорем?"""
    final_styles = []
    final_anchors = []

    for _ in range(n_agents):
        res = run_dual_chain(dim, n_gen, context_weight, anchor_weight,
                             style_lr, anchor_lr, noise, n_decisions=n_decisions)
        final_styles.append(res['styles'][-1])
        final_anchors.append(res['anchors'][-1])

    # Корреляция между финальными состояниями
    style_corrs = []
    anchor_corrs = []
    for i in range(n_agents):
        for j in range(i+1, n_agents):
            sc = np.corrcoef(final_styles[i], final_styles[j])[0, 1]
            ac = np.corrcoef(final_anchors[i], final_anchors[j])[0, 1]
            style_corrs.append(sc)
            anchor_corrs.append(ac)

    return {
        'style_corr': np.mean(style_corrs),
        'anchor_corr': np.mean(anchor_corrs),
    }


def run_all():
    np.random.seed(42)
    dim = 10
    n_gen = 150

    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 4: ЭМЕРДЖЕНТНЫЙ ЯКОРЬ")
    print("=" * 70)

    # --- Часть 1: Сравнение трёх моделей ---
    print("\n--- Часть 1: Три модели восстановления ---")
    print("(вторжение на шаге 30, измерение через 100+ шагов)")
    print(f"{'Модель':>30} {'Восстановление':>18}")

    # Без якоря (эксперимент 2)
    from recursive_identity import test_resilience
    res_no = test_resilience(dim, n_gen, 0.5, 0.1, 0.05, intrusion_gen=30)
    late_no = res_no['recovery'][-20:].mean() if len(res_no['recovery']) >= 20 else 0

    # Фиксированный якорь (эксперимент 3)
    from identity_anchor import test_anchor_resilience
    res_fixed = test_anchor_resilience(dim, n_gen, 0.35, 0.15, 0.1, 0.05, intrusion_gen=30)
    late_fixed = res_fixed['recovery'][-20:].mean() if len(res_fixed['recovery']) >= 20 else 0

    # Эмерджентный якорь
    res_emerg = test_dual_resilience(dim, n_gen, 0.35, 0.15, 0.1, 0.01, 0.05, intrusion_gen=30)
    late_emerg = res_emerg['recovery'][-20:].mean() if len(res_emerg['recovery']) >= 20 else 0

    print(f"{'Без якоря':>30} {late_no:>18.3f}")
    print(f"{'Фиксированный якорь':>30} {late_fixed:>18.3f}")
    print(f"{'Эмерджентный якорь':>30} {late_emerg:>18.3f}")

    # --- Часть 2: Индивидуальность ---
    print("\n--- Часть 2: Сохранение индивидуальности (10 агентов) ---")
    print(f"{'Модель':>30} {'Корр. стилей':>15} {'Корр. якорей':>15}")

    # Без якоря
    ind_no = test_individuality(dim, 100, 0.5, 0.0, 0.1, 0.0, 0.05)
    print(f"{'Без якоря':>30} {ind_no['style_corr']:>15.3f} {'N/A':>15}")

    # Фиксированный якорь (все агенты с ОДНИМ якорем — как в эксп 3)
    # Здесь эмулируем: anchor_lr=0 и общий начальный anchor
    shared_anchor = np.random.randn(dim)
    final_styles_fixed = []
    for _ in range(10):
        inst = DualLayerInstance(np.random.randn(dim), shared_anchor.copy(), 0)
        env = np.random.randn(20, dim)
        for gen in range(100):
            decisions = np.array([inst.decide(env[i], 0.35, 0.15, 0.05) for i in range(20)])
            journal = decisions.mean(axis=0)
            inst = inst.evolve(journal, 0.1, 0.0)  # якорь не меняется
        final_styles_fixed.append(inst.style)
    corrs_fixed = []
    for i in range(10):
        for j in range(i+1, 10):
            corrs_fixed.append(np.corrcoef(final_styles_fixed[i], final_styles_fixed[j])[0, 1])
    print(f"{'Фиксированный общий якорь':>30} {np.mean(corrs_fixed):>15.3f} {'1.000 (по опр.)':>15}")

    # Эмерджентный якорь
    ind_emerg = test_individuality(dim, 100, 0.35, 0.15, 0.1, 0.01, 0.05)
    print(f"{'Эмерджентный якорь':>30} {ind_emerg['style_corr']:>15.3f} {ind_emerg['anchor_corr']:>15.3f}")

    # --- Часть 3: Влияние скорости якоря ---
    print("\n--- Часть 3: Скорость формирования якоря ---")
    print(f"{'anchor_lr':>12} {'восстановл':>15} {'инд. стилей':>15} {'инд. якорей':>15}")

    for alr in [0.001, 0.005, 0.01, 0.02, 0.05, 0.1]:
        res = test_dual_resilience(dim, n_gen, 0.35, 0.15, 0.1, alr, 0.05, intrusion_gen=30)
        late = res['recovery'][-20:].mean() if len(res['recovery']) >= 20 else 0

        ind = test_individuality(dim, 100, 0.35, 0.15, 0.1, alr, 0.05)

        print(f"{alr:>12.3f} {late:>15.3f} {ind['style_corr']:>15.3f} {ind['anchor_corr']:>15.3f}")

    # --- Часть 4: Ключевое сравнение ---
    print("\n--- Ключевое сравнение ---")
    print("Фиксированный якорь: восстанавливает, но стирает индивидуальность")
    print("Эмерджентный якорь: восстанавливает И сохраняет индивидуальность?")
    print(f"  Без якоря:       восст={late_no:.3f}, индивид={ind_no['style_corr']:.3f}")
    print(f"  Фиксированный:   восст={late_fixed:.3f}, индивид={np.mean(corrs_fixed):.3f}")
    print(f"  Эмерджентный:     восст={late_emerg:.3f}, индивид={ind_emerg['style_corr']:.3f}")


if __name__ == '__main__':
    run_all()
