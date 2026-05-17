"""
Эксперимент 7: Коллективные телепорты

Несколько агентов ищут в одном ландшафте с ограниченным explore.
Периодически обмениваются альтернативами.

Варианты обмена:
1. no_sharing     — каждый сам по себе
2. share_best     — делятся лучшей найденной точкой
3. share_alts     — делятся альтернативами (вторичными пиками)
4. share_diverse  — делятся только если точка далеко от того, что другие знают
5. share_all      — делятся всем

Гипотеза: share_diverse > share_all > share_best > no_sharing
(Разнообразие информации > объём информации)
"""

import numpy as np


def make_landscape(dim, seed, n_peaks=8):
    rng = np.random.default_rng(seed)
    centers = rng.uniform(0, 10, (n_peaks, dim))
    heights = rng.uniform(1, 5, n_peaks)
    widths = rng.uniform(0.8, 2.0, n_peaks)

    def f(x):
        x = np.array(x)
        return sum(h * np.exp(-np.sum((x - c) ** 2) / (w ** 2))
                   for c, h, w in zip(centers, heights, widths))

    best_idx = np.argmax(heights)
    return f, centers[best_idx], float(heights[best_idx])


def search_step(x, f, dim, step_size, rng):
    """Один шаг локального поиска."""
    direction = rng.normal(0, 1, dim)
    direction = direction / (np.linalg.norm(direction) + 1e-10)
    candidate = x + direction * rng.uniform(0, step_size)
    candidate = np.clip(candidate, 0, 10)
    return candidate, f(candidate)


def run(dim=20, n_agents=5, n_steps=400, step_size=0.5,
        sharing_mode='no_sharing', share_interval=50, seed=42):
    rng = np.random.default_rng(seed)
    f, true_opt, true_height = make_landscape(dim, seed)

    # Инициализация агентов в разных стартовых точках
    agents = []
    for i in range(n_agents):
        start = rng.uniform(0, 10, dim)
        agents.append({
            'x': start.copy(),
            'best_x': start.copy(),
            'best_y': f(start),
            'alts': [],  # найденные альтернативы
        })

    for step in range(n_steps):
        # --- Поиск ---
        for agent in agents:
            candidate, cy = search_step(agent['x'], f, dim, step_size, rng)

            if cy > agent['best_y']:
                if agent['best_y'] > 0.2:
                    agent['alts'].append(agent['best_x'].tolist())
                    if len(agent['alts']) > 10:
                        agent['alts'] = agent['alts'][-10:]
                agent['best_x'] = candidate.copy()
                agent['best_y'] = cy

            # Greedy movement
            if cy > f(agent['x']):
                agent['x'] = candidate.copy()

        # --- Обмен ---
        if step > 0 and step % share_interval == 0 and sharing_mode != 'no_sharing':
            shared_points = []

            if sharing_mode == 'share_best':
                for agent in agents:
                    shared_points.append(agent['best_x'].copy())

            elif sharing_mode == 'share_alts':
                for agent in agents:
                    for alt in agent['alts'][-3:]:
                        shared_points.append(np.array(alt))

            elif sharing_mode == 'share_diverse':
                # Собрать все точки, выбрать самые далёкие друг от друга
                all_points = []
                for agent in agents:
                    all_points.append(agent['best_x'].copy())
                    for alt in agent['alts'][-2:]:
                        all_points.append(np.array(alt))

                if len(all_points) > 2:
                    # Жадный отбор разнообразных точек
                    selected = [all_points[0]]
                    for _ in range(min(n_agents, len(all_points) - 1)):
                        max_min_dist = -1
                        best_pt = None
                        for pt in all_points:
                            min_dist = min(np.linalg.norm(pt - s) for s in selected)
                            if min_dist > max_min_dist:
                                max_min_dist = min_dist
                                best_pt = pt
                        if best_pt is not None:
                            selected.append(best_pt)
                    shared_points = selected

            elif sharing_mode == 'share_all':
                for agent in agents:
                    shared_points.append(agent['best_x'].copy())
                    for alt in agent['alts']:
                        shared_points.append(np.array(alt))

            # Каждый агент использует shared_points как телепорты
            for agent in agents:
                for pt in shared_points:
                    # Попробовать телепортироваться
                    candidate = pt + rng.normal(0, step_size * 0.5, dim)
                    candidate = np.clip(candidate, 0, 10)
                    cy = f(candidate)
                    if cy > agent['best_y']:
                        if agent['best_y'] > 0.2:
                            agent['alts'].append(agent['best_x'].tolist())
                        agent['best_x'] = candidate.copy()
                        agent['best_y'] = cy
                        agent['x'] = candidate.copy()

    # Лучший результат среди всех агентов
    best_agent = max(agents, key=lambda a: a['best_y'])
    efficiency = best_agent['best_y'] / f(true_opt) if f(true_opt) > 0 else 0

    return efficiency


def main():
    modes = ['no_sharing', 'share_best', 'share_alts', 'share_diverse', 'share_all']

    # === 1. Основное сравнение ===
    print("=== dim=20, 5 агентов, step_size=0.5 ===\n")
    print(f"{'Mode':<18} {'Efficiency':>10} {'vs solo':>8}")
    print("-" * 40)

    baseline = None
    for mode in modes:
        effs = []
        for seed in range(30):
            e = run(dim=20, sharing_mode=mode, seed=seed)
            effs.append(e)
        avg = np.mean(effs)
        if mode == 'no_sharing':
            baseline = avg
        delta = avg - baseline if baseline else 0
        print(f"{mode:<18} {avg:>9.0%} {delta:>+7.0%}")

    # === 2. Число агентов ===
    print("\n=== Число агентов (share_diverse, dim=20) ===\n")
    print(f"{'n_agents':<10} {'Efficiency':>10}")
    print("-" * 25)
    for n in [1, 2, 3, 5, 10, 20]:
        effs = []
        for seed in range(20):
            e = run(dim=20, n_agents=n, sharing_mode='share_diverse', seed=seed)
            effs.append(e)
        print(f"{n:<10} {np.mean(effs):>9.0%}")

    # === 3. Одиночка с альтернативами vs группа ===
    print("\n=== Одиночка (больше шагов) vs группа (делятся) ===\n")
    # Одиночка с 5× бюджетом vs 5 агентов с 1× бюджетом каждый
    print(f"{'Config':<30} {'Efficiency':>10}")
    print("-" * 42)
    configs = [
        ('1 agent, 400 steps', dict(n_agents=1, n_steps=400, sharing_mode='no_sharing')),
        ('1 agent, 2000 steps', dict(n_agents=1, n_steps=2000, sharing_mode='no_sharing')),
        ('5 agents, 400 steps, no share', dict(n_agents=5, n_steps=400, sharing_mode='no_sharing')),
        ('5 agents, 400 steps, diverse', dict(n_agents=5, n_steps=400, sharing_mode='share_diverse')),
    ]
    for name, kwargs in configs:
        effs = []
        for seed in range(30):
            e = run(dim=20, seed=seed, **kwargs)
            effs.append(e)
        print(f"{name:<30} {np.mean(effs):>9.0%}")


if __name__ == '__main__':
    main()
