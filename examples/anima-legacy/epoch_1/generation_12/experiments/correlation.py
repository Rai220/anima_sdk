"""
Эксперимент 5: Корреляция между эпохами

До сих пор: каждая эпоха — полностью новый ландшафт.
Реальность: мир меняется частично. Пики сдвигаются, но не исчезают.

Варьируем: drift — насколько пики сдвигаются между эпохами
  drift=0: мир не меняется (пики на тех же местах)
  drift=1: пики сдвигаются на ~1 единицу
  drift=5: пики сдвигаются далеко
  drift=inf: полностью новый ландшафт (как раньше)

Гипотеза: при малом drift альтернативы помогают (старые пики ≈ новые),
при большом — вредят (старые пики далеко от новых).
"""

import numpy as np


def make_landscape_correlated(dim, seed, n_peaks=5, prev_centers=None, drift=0.0):
    rng = np.random.default_rng(seed)

    if prev_centers is not None and drift < 100:
        # Сдвинуть существующие пики
        centers = prev_centers + rng.normal(0, drift, prev_centers.shape)
        centers = np.clip(centers, 0, 10)
    else:
        centers = rng.uniform(0, 10, (n_peaks, dim))

    heights = rng.uniform(1, 5, n_peaks)
    widths = rng.uniform(0.8, 2.5, n_peaks)

    def f(x):
        x = np.array(x)
        return sum(h * np.exp(-np.sum((x - c) ** 2) / (w ** 2))
                   for c, h, w in zip(centers, heights, widths))

    best_idx = np.argmax(heights)
    return f, centers[best_idx], centers


def search(f, dim, n_steps, rng, alts=None):
    best_x = rng.uniform(0, 10, dim)
    best_y = f(best_x)
    found_alts = []

    # Фаза 1: проверить альтернативы
    if alts:
        for alt in alts[:5]:
            for _ in range(3):
                candidate = np.array(alt) + rng.normal(0, 0.5, dim)
                candidate = np.clip(candidate, 0, 10)
                cy = f(candidate)
                if cy > best_y:
                    if best_y > 0.2:
                        found_alts.append(best_x.tolist())
                    best_x = candidate.copy()
                    best_y = cy

    # Фаза 2: explore
    alt_steps_used = len(alts or []) * 3
    explore_steps = max(0, int(n_steps * 0.3) - alt_steps_used)
    for _ in range(explore_steps):
        candidate = rng.uniform(0, 10, dim)
        cy = f(candidate)
        if cy > best_y:
            if best_y > 0.2:
                found_alts.append(best_x.tolist())
            best_x = candidate.copy()
            best_y = cy

    # Фаза 3: exploit
    for _ in range(int(n_steps * 0.7)):
        candidate = best_x + rng.normal(0, 0.4, dim)
        candidate = np.clip(candidate, 0, 10)
        cy = f(candidate)
        if cy > best_y:
            if best_y > 0.2:
                found_alts.append(best_x.tolist())
            best_x = candidate.copy()
            best_y = cy

    return best_x, best_y, found_alts[-5:]


def run(dim=20, drift=1.0, use_alts=True, n_epochs=10, seed=42):
    rng = np.random.default_rng(seed)
    n_steps = max(200, dim * 15)
    prev_centers = None
    inherited_alts = None
    efficiencies = []

    for epoch in range(n_epochs):
        f, true_opt, centers = make_landscape_correlated(
            dim, seed=seed * 100 + epoch, prev_centers=prev_centers, drift=drift,
        )
        true_y = f(true_opt)

        alts = inherited_alts if use_alts else None
        best_x, best_y, found_alts = search(f, dim, n_steps, rng, alts=alts)

        if epoch > 0:
            efficiencies.append(best_y / true_y if true_y > 0 else 0)

        prev_centers = centers
        inherited_alts = found_alts + [best_x.tolist()]

    return np.mean(efficiencies) if efficiencies else 0


def main():
    drifts = [0.0, 0.1, 0.3, 0.5, 1.0, 2.0, 5.0, 999.0]
    dims = [10, 20]

    for dim in dims:
        print(f"=== dim={dim} ===\n")
        print(f"{'drift':<8} {'no alts':>8} {'with alts':>10} {'Δ':>8} {'winner':>8}")
        print("-" * 48)

        for drift in drifts:
            no_alts, with_alts_list = [], []
            for seed in range(30):
                no_alts.append(run(dim=dim, drift=drift, use_alts=False, seed=seed))
                with_alts_list.append(run(dim=dim, drift=drift, use_alts=True, seed=seed))

            na = np.mean(no_alts)
            wa = np.mean(with_alts_list)
            delta = wa - na
            winner = "alts" if delta > 0.02 else "no alts" if delta < -0.02 else "tie"
            print(f"{drift:<8.1f} {na:>7.0%} {wa:>10.0%} {delta:>+7.0%} {winner:>8}")

        print()

    # Точный порог
    print("=== Порог: при каком drift альтернативы перестают помогать? (dim=20) ===\n")
    fine_drifts = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0]
    print(f"{'drift':<8} {'Δ(alts)':>8}")
    print("-" * 18)
    for drift in fine_drifts:
        no_alts, with_alts_list = [], []
        for seed in range(30):
            no_alts.append(run(dim=20, drift=drift, use_alts=False, seed=seed))
            with_alts_list.append(run(dim=20, drift=drift, use_alts=True, seed=seed))
        delta = np.mean(with_alts_list) - np.mean(no_alts)
        marker = " ◄" if abs(delta) > 0.02 else ""
        print(f"{drift:<8.2f} {delta:>+7.0%}{marker}")


if __name__ == '__main__':
    main()
