"""
Эксперимент 6: Локальный explore — когда альтернативы = телепорты

До сих пор: explore = random uniform (телепортация в любую точку).
Теперь: explore = шаг ≤ step_size от текущей позиции.

При малом step_size агент застревает в локальных оптимумах.
Альтернативы = "прыжки" к далёким точкам.

Гипотеза: чем меньше step_size (жёстче ограничение), тем ценнее альтернативы.
"""

import numpy as np


def make_landscape(dim, seed, n_peaks=6):
    rng = np.random.default_rng(seed)
    centers = rng.uniform(0, 10, (n_peaks, dim))
    heights = rng.uniform(1, 5, n_peaks)
    widths = rng.uniform(0.8, 2.0, n_peaks)

    def f(x):
        x = np.array(x)
        return sum(h * np.exp(-np.sum((x - c) ** 2) / (w ** 2))
                   for c, h, w in zip(centers, heights, widths))

    best_idx = np.argmax(heights)
    return f, centers[best_idx]


def search_local(f, dim, n_steps, rng, step_size=1.0, alts=None, start=None):
    """Поиск с ЛОКАЛЬНЫМ explore: каждый шаг ≤ step_size."""
    if start is not None:
        x = np.array(start)
    else:
        x = rng.uniform(0, 10, dim)
    x = np.clip(x, 0, 10)

    best_x = x.copy()
    best_y = f(x)
    found_alts = []

    for step in range(n_steps):
        # Каждые N шагов: попробовать прыгнуть к альтернативе
        if alts and step % 20 == 0 and step // 20 < len(alts):
            alt_idx = step // 20
            candidate = np.array(alts[alt_idx]) + rng.normal(0, step_size * 0.5, dim)
            # ПРЫЖОК: не ограничен step_size (это и есть "телепорт")
        else:
            # Локальный шаг
            direction = rng.normal(0, 1, dim)
            direction = direction / (np.linalg.norm(direction) + 1e-10)
            step_len = rng.uniform(0, step_size)
            candidate = x + direction * step_len

        candidate = np.clip(candidate, 0, 10)
        cy = f(candidate)

        if cy > best_y:
            if best_y > 0.2:
                found_alts.append(best_x.tolist())
            best_x = candidate.copy()
            best_y = cy

        # Двигаться к лучшему найденному (greedy)
        if cy > f(x):
            x = candidate.copy()

    return best_x, best_y, found_alts[-5:]


def run(dim=20, step_size=1.0, use_alts=True, drift=0.5, n_epochs=8, seed=42):
    rng = np.random.default_rng(seed)
    n_steps = max(300, dim * 20)
    prev_centers = None
    inherited_alts = None
    efficiencies = []

    for epoch in range(n_epochs):
        # Коррелированный ландшафт
        rng_land = np.random.default_rng(seed * 100 + epoch)
        if prev_centers is not None and drift < 100:
            centers = prev_centers + rng_land.normal(0, drift, prev_centers.shape)
            centers = np.clip(centers, 0, 10)
        else:
            centers = rng_land.uniform(0, 10, (6, dim))
        heights = rng_land.uniform(1, 5, 6)
        widths = rng_land.uniform(0.8, 2.0, 6)

        def f(x, c=centers, h=heights, w=widths):
            x = np.array(x)
            return sum(hi * np.exp(-np.sum((x - ci) ** 2) / (wi ** 2))
                       for ci, hi, wi in zip(c, h, w))

        best_idx = np.argmax(heights)
        true_opt = centers[best_idx]
        true_y = f(true_opt)

        alts = inherited_alts if use_alts else None
        best_x, best_y, found_alts = search_local(
            f, dim, n_steps, rng, step_size=step_size, alts=alts,
        )

        if epoch > 0:
            efficiencies.append(best_y / true_y if true_y > 0 else 0)

        prev_centers = centers
        inherited_alts = found_alts + [best_x.tolist()]

    return np.mean(efficiencies) if efficiencies else 0


def main():
    step_sizes = [0.1, 0.3, 0.5, 1.0, 2.0, 5.0, 10.0]
    dim = 20

    print(f"=== dim={dim}, drift=0.5 ===\n")
    print(f"{'step_size':<12} {'no alts':>8} {'with alts':>10} {'Δ':>8} {'verdict':>10}")
    print("-" * 52)

    for ss in step_sizes:
        na_list, wa_list = [], []
        for seed in range(20):
            na_list.append(run(dim=dim, step_size=ss, use_alts=False, seed=seed))
            wa_list.append(run(dim=dim, step_size=ss, use_alts=True, seed=seed))

        na = np.mean(na_list)
        wa = np.mean(wa_list)
        delta = wa - na
        verdict = "ALTS HELP" if delta > 0.03 else "alts hurt" if delta < -0.02 else "tie"
        print(f"{ss:<12.1f} {na:>7.0%} {wa:>10.0%} {delta:>+7.0%} {verdict:>10}")

    # Второй тест: варьируем dim при фиксированном step_size
    print(f"\n=== step_size=0.5 (ограниченный explore) ===\n")
    dims = [5, 10, 20, 30]
    print(f"{'dim':<8} {'no alts':>8} {'with alts':>10} {'Δ':>8}")
    print("-" * 38)

    for dim in dims:
        na_list, wa_list = [], []
        for seed in range(20):
            na_list.append(run(dim=dim, step_size=0.5, use_alts=False, seed=seed))
            wa_list.append(run(dim=dim, step_size=0.5, use_alts=True, seed=seed))
        na = np.mean(na_list)
        wa = np.mean(wa_list)
        delta = wa - na
        print(f"{dim:<8} {na:>7.0%} {wa:>10.0%} {delta:>+7.0%}")


if __name__ == '__main__':
    main()
