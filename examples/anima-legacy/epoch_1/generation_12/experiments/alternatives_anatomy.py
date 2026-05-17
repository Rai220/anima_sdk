"""
Эксперимент 4: Анатомия альтернатив

Эксп. 2 показал: при dim≥20 полная структура (включая альтернативы) помогает.
Эксп. 3 показал: негативное знание бесполезно.
→ Альтернативы — ключевой компонент.

Вопросы:
1. Сколько альтернатив нужно? (1, 3, 5, 10, 20)
2. Качество альтернатив: рандомные vs найденные поиском vs вторичные пики?
3. Как это масштабируется с размерностью?
"""

import numpy as np


def make_landscape(dim, seed, n_peaks=6):
    rng = np.random.default_rng(seed)
    centers = rng.uniform(0, 10, (n_peaks, dim))
    heights = rng.uniform(1, 5, n_peaks)
    widths = rng.uniform(0.8, 2.5, n_peaks)

    def f(x):
        x = np.array(x)
        return sum(h * np.exp(-np.sum((x - c) ** 2) / (w ** 2))
                   for c, h, w in zip(centers, heights, widths))

    best_idx = np.argmax(heights)
    return f, centers[best_idx], centers, heights


def search_with_alts(f, dim, n_steps, rng, alts=None, n_explore_from_alts=5):
    """Поиск: explore from alternatives, then exploit best."""
    best_x = rng.uniform(0, 10, dim)
    best_y = f(best_x)
    found_alts = []

    # Фаза 1: проверить альтернативы
    if alts is not None:
        for alt in alts:
            for _ in range(n_explore_from_alts):
                candidate = np.array(alt) + rng.normal(0, 0.8, dim)
                candidate = np.clip(candidate, 0, 10)
                cy = f(candidate)
                if cy > best_y:
                    if best_y > 0.3:
                        found_alts.append(best_x.tolist())
                    best_x = candidate.copy()
                    best_y = cy

    # Фаза 2: explore
    explore_steps = int(n_steps * 0.3)
    for _ in range(explore_steps):
        candidate = rng.uniform(0, 10, dim)
        cy = f(candidate)
        if cy > best_y:
            if best_y > 0.3:
                found_alts.append(best_x.tolist())
            best_x = candidate.copy()
            best_y = cy

    # Фаза 3: exploit
    exploit_steps = n_steps - explore_steps - (len(alts or []) * n_explore_from_alts)
    for _ in range(max(0, exploit_steps)):
        candidate = best_x + rng.normal(0, 0.4, dim)
        candidate = np.clip(candidate, 0, 10)
        cy = f(candidate)
        if cy > best_y:
            if best_y > 0.3:
                found_alts.append(best_x.tolist())
            best_x = candidate.copy()
            best_y = cy

    return best_x, best_y, found_alts[-10:]  # max 10 альтернатив


def run_test(dim, n_alts_to_pass, alt_quality='found', n_epochs=8, seed=42):
    """
    alt_quality:
      'found'  — альтернативы = вторичные пики из предыдущего поиска
      'random' — случайные точки
      'true_peaks' — настоящие центры пиков (идеальная информация)
    """
    rng = np.random.default_rng(seed)
    n_steps = max(200, dim * 15)
    inherited_alts = None
    efficiencies = []

    for epoch in range(n_epochs):
        f, true_opt, centers, heights = make_landscape(dim, seed=seed * 100 + epoch)
        true_y = f(true_opt)

        # Подготовить альтернативы в зависимости от качества
        if alt_quality == 'random' and epoch > 0:
            alts_to_use = [rng.uniform(0, 10, dim).tolist() for _ in range(n_alts_to_pass)]
        elif alt_quality == 'true_peaks' and epoch > 0:
            # Подсмотреть настоящие пики прошлой эпохи (читерство — для калибровки)
            prev_f, _, prev_centers, prev_heights = make_landscape(dim, seed=seed * 100 + epoch - 1)
            sorted_idx = np.argsort(-prev_heights)
            alts_to_use = [prev_centers[i].tolist() for i in sorted_idx[:n_alts_to_pass]]
        elif inherited_alts is not None:
            alts_to_use = inherited_alts[:n_alts_to_pass]
        else:
            alts_to_use = None

        best_x, best_y, found_alts = search_with_alts(
            f, dim, n_steps, rng, alts=alts_to_use,
        )

        if epoch > 0:
            efficiencies.append(best_y / true_y if true_y > 0 else 0)

        inherited_alts = found_alts

    return np.mean(efficiencies) if efficiencies else 0


def main():
    # === 1. Количество альтернатив ===
    print("=== 1. Сколько альтернатив нужно? ===\n")
    n_alts_list = [0, 1, 2, 3, 5, 10, 20]
    dims = [5, 10, 20]

    header = f"{'n_alts':<8}" + "".join(f"dim={d:<10}" for d in dims)
    print(header)
    print("-" * len(header))

    for n_alts in n_alts_list:
        row = f"{n_alts:<8}"
        for dim in dims:
            effs = []
            for seed in range(20):
                e = run_test(dim, n_alts, alt_quality='found', seed=seed)
                effs.append(e)
            row += f"{np.mean(effs):<10.0%}"
        print(row)

    # === 2. Качество альтернатив ===
    print("\n=== 2. Качество альтернатив (dim=20, n_alts=5) ===\n")
    qualities = ['found', 'random', 'true_peaks']
    print(f"{'Quality':<14} {'Efficiency':>10}")
    print("-" * 28)
    for quality in qualities:
        effs = []
        for seed in range(30):
            e = run_test(20, 5, alt_quality=quality, seed=seed)
            effs.append(e)
        print(f"{quality:<14} {np.mean(effs):>9.0%}")

    # Baseline: method only (0 alts)
    effs_baseline = []
    for seed in range(30):
        e = run_test(20, 0, seed=seed)
        effs_baseline.append(e)
    print(f"{'no alts':<14} {np.mean(effs_baseline):>9.0%}")

    # === 3. Закон убывающей отдачи? ===
    print("\n=== 3. Маргинальная ценность N-й альтернативы (dim=20) ===\n")
    prev_eff = 0
    for n_alts in [0, 1, 2, 3, 5, 10, 20]:
        effs = []
        for seed in range(30):
            e = run_test(20, n_alts, alt_quality='found', seed=seed)
            effs.append(e)
        avg = np.mean(effs)
        delta = avg - prev_eff if n_alts > 0 else 0
        print(f"  n_alts={n_alts:<4} efficiency={avg:.0%}  Δ={delta:+.0%}")
        prev_eff = avg


if __name__ == '__main__':
    main()
