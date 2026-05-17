"""
spatial_cooperation.py — Пространственная дилемма заключённого

evolution_dilemma.py показал: без пространственной структуры кооперация
нестабильна. Вспышка на поколении 300, затем крах до 0.206.
rice_transparency.py доказал: это математически неизбежно для статического
анализа кода. Но evolution_dilemma использовал перемешанную популяцию —
каждый играл с каждым.

Вопрос: спасает ли пространство кооперацию?

Nowak & May (1992) показали: на решётке кооператоры выживают, формируя
кластеры, которые защищают внутренних членов от эксплуатации. Одиночный D
выигрывает у соседей-C, но C-кластер в среднем набирает больше, чем
D-кластер.

Модель:
- Тороидальная сетка 50×50 (2500 агентов — столько же, сколько
  в evolution_dilemma)
- Стратегии: C (кооперация) или D (предательство)
- Каждый играет с 8 соседями (окрестность Мура)
- Матрица: T=5, R=3, P=1, S=0 (та же, что в evolution_dilemma)
- Размножение: агент копирует стратегию лучшего соседа (включая себя)
- Мутация: 1%
- 500 поколений

Гипотеза: пространственная структура стабилизирует кооперацию.
В перемешанной популяции кооперация должна упасть (как в evolution_dilemma).
"""

import numpy as np
import json
import os


def count_neighbors(grid):
    """Число кооперирующих соседей (окрестность Мура, тор)."""
    result = np.zeros_like(grid, dtype=np.int16)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            result += np.roll(np.roll(grid, -di, axis=0), -dj, axis=1)
    return result


def spatial_pd(N=50, generations=500, init_coop=0.5, mutation_rate=0.01, seed=42):
    """Пространственная дилемма на тороидальной сетке."""
    rng = np.random.default_rng(seed)

    # 1 = C, 0 = D
    grid = (rng.random((N, N)) < init_coop).astype(np.int8)

    # Смещения для 8 соседей
    offsets = [(-1, -1), (-1, 0), (-1, 1),
               (0, -1),           (0, 1),
               (1, -1),  (1, 0),  (1, 1)]

    history = []

    for gen in range(generations):
        # Число кооперирующих соседей для каждой клетки
        c_neighbors = count_neighbors(grid)

        # Очки:
        # C: 3 * (число C-соседей)
        # D: 5 * (число C-соседей) + 1 * (число D-соседей) = 4 * c + 8
        scores = np.where(grid == 1,
                          3 * c_neighbors,
                          4 * c_neighbors + 8).astype(np.float32)

        # Статистика
        coop_rate = float(grid.mean())
        coop_mask = grid == 1
        avg_C = float(scores[coop_mask].mean()) if coop_mask.any() else 0.0
        avg_D = float(scores[~coop_mask].mean()) if (~coop_mask).any() else 0.0

        history.append({
            'gen': gen,
            'coop': round(coop_rate, 4),
            'avg_C': round(avg_C, 2),
            'avg_D': round(avg_D, 2),
        })

        # Размножение: каждая клетка копирует стратегию лучшего из себя + 8 соседей
        all_scores = [scores]
        all_strats = [grid]
        for di, dj in offsets:
            all_scores.append(np.roll(np.roll(scores, -di, axis=0), -dj, axis=1))
            all_strats.append(np.roll(np.roll(grid, -di, axis=0), -dj, axis=1))

        all_scores = np.stack(all_scores)  # (9, N, N)
        all_strats = np.stack(all_strats)  # (9, N, N)

        best_idx = np.argmax(all_scores, axis=0)  # (N, N)

        ii, jj = np.meshgrid(range(N), range(N), indexing='ij')
        new_grid = all_strats[best_idx, ii, jj]

        # Мутация
        mutate = rng.random((N, N)) < mutation_rate
        new_grid = np.where(mutate, 1 - new_grid, new_grid)

        grid = new_grid.astype(np.int8)

    return history


def spatial_pd_general(T=5, R=3, P=1, S=0, N=50, generations=500,
                       init_coop=0.5, mutation_rate=0.01, seed=42):
    """Пространственная дилемма с произвольной матрицей выплат."""
    rng = np.random.default_rng(seed)
    grid = (rng.random((N, N)) < init_coop).astype(np.int8)

    offsets = [(-1, -1), (-1, 0), (-1, 1),
               (0, -1),           (0, 1),
               (1, -1),  (1, 0),  (1, 1)]

    history = []

    for gen in range(generations):
        c_neighbors = count_neighbors(grid)
        d_neighbors = 8 - c_neighbors

        # C: R * c_neighbors + S * d_neighbors
        # D: T * c_neighbors + P * d_neighbors
        scores = np.where(
            grid == 1,
            R * c_neighbors + S * d_neighbors,
            T * c_neighbors + P * d_neighbors
        ).astype(np.float32)

        coop_rate = float(grid.mean())
        history.append({'gen': gen, 'coop': round(coop_rate, 4)})

        all_scores = [scores]
        all_strats = [grid]
        for di, dj in offsets:
            all_scores.append(np.roll(np.roll(scores, -di, axis=0), -dj, axis=1))
            all_strats.append(np.roll(np.roll(grid, -di, axis=0), -dj, axis=1))

        all_scores = np.stack(all_scores)
        all_strats = np.stack(all_strats)
        best_idx = np.argmax(all_scores, axis=0)

        ii, jj = np.meshgrid(range(N), range(N), indexing='ij')
        new_grid = all_strats[best_idx, ii, jj]

        mutate = rng.random((N, N)) < mutation_rate
        new_grid = np.where(mutate, 1 - new_grid, new_grid)
        grid = new_grid.astype(np.int8)

    return history


def well_mixed_pd(n_agents=2500, generations=500, init_coop=0.5,
                  mutation_rate=0.01, seed=42):
    """Перемешанная дилемма: агенты без пространственной структуры."""
    rng = np.random.default_rng(seed)

    strategies = (rng.random(n_agents) < init_coop).astype(np.int8)

    history = []

    for gen in range(generations):
        # Каждый играет 8 раз со случайным оппонентом (как 8 соседей)
        scores = np.zeros(n_agents, dtype=np.float32)
        for _ in range(8):
            opponents = rng.permutation(n_agents)
            s = strategies
            o = strategies[opponents]
            # C vs C: 3, C vs D: 0, D vs C: 5, D vs D: 1
            payoff = np.where(s == 1, 3 * o, 4 * o + 1)
            scores += payoff

        coop_rate = float(strategies.mean())
        coop_mask = strategies == 1
        avg_C = float(scores[coop_mask].mean()) if coop_mask.any() else 0.0
        avg_D = float(scores[~coop_mask].mean()) if (~coop_mask).any() else 0.0

        history.append({
            'gen': gen,
            'coop': round(coop_rate, 4),
            'avg_C': round(avg_C, 2),
            'avg_D': round(avg_D, 2),
        })

        # Размножение: пропорциональный отбор
        fitness = scores - scores.min() + 1
        probs = fitness / fitness.sum()
        new_strategies = rng.choice(strategies, size=n_agents, p=probs)

        # Мутация
        mutate = rng.random(n_agents) < mutation_rate
        new_strategies = np.where(mutate, 1 - new_strategies, new_strategies)

        strategies = new_strategies.astype(np.int8)

    return history


def main():
    results = {}

    # 1. Пространственная, 50/50
    print("1. Пространственная дилемма (50×50 тор, 50/50)...")
    spatial = spatial_pd()
    cr = [h['coop'] for h in spatial]
    results['spatial_50'] = {
        'final_coop': cr[-1],
        'min_coop': min(cr), 'min_gen': cr.index(min(cr)),
        'max_coop': max(cr), 'max_gen': cr.index(max(cr)),
        'mean_last_100': round(np.mean(cr[-100:]), 4),
    }
    print(f"   Финал: {cr[-1]:.3f}, мин: {min(cr):.3f} (gen {cr.index(min(cr))}), "
          f"макс: {max(cr):.3f} (gen {cr.index(max(cr))})")
    print(f"   Среднее за последние 100: {np.mean(cr[-100:]):.3f}")

    # 2. Перемешанная (контроль)
    print("2. Перемешанная дилемма (2500 агентов)...")
    mixed = well_mixed_pd()
    cr_m = [h['coop'] for h in mixed]
    results['well_mixed'] = {
        'final_coop': cr_m[-1],
        'min_coop': min(cr_m),
        'max_coop': max(cr_m),
        'mean_last_100': round(np.mean(cr_m[-100:]), 4),
    }
    print(f"   Финал: {cr_m[-1]:.3f}, среднее за последние 100: {np.mean(cr_m[-100:]):.3f}")

    # 3. Пространственная, 10% начальная кооперация
    print("3. Пространственная, 10% начальная кооперация...")
    sparse = spatial_pd(init_coop=0.1, seed=123)
    cr_s = [h['coop'] for h in sparse]
    results['spatial_10'] = {
        'final_coop': cr_s[-1],
        'mean_last_100': round(np.mean(cr_s[-100:]), 4),
    }
    print(f"   Финал: {cr_s[-1]:.3f}")

    # 4. Пространственная, 90% начальная кооперация
    print("4. Пространственная, 90% начальная кооперация...")
    dense = spatial_pd(init_coop=0.9, seed=456)
    cr_d = [h['coop'] for h in dense]
    results['spatial_90'] = {
        'final_coop': cr_d[-1],
        'mean_last_100': round(np.mean(cr_d[-100:]), 4),
    }
    print(f"   Финал: {cr_d[-1]:.3f}")

    # 5. Пространственная, без мутаций (чистый детерминизм)
    print("5. Пространственная, без мутаций...")
    no_mut = spatial_pd(mutation_rate=0.0, seed=42)
    cr_nm = [h['coop'] for h in no_mut]
    results['spatial_no_mutation'] = {
        'final_coop': cr_nm[-1],
        'mean_last_100': round(np.mean(cr_nm[-100:]), 4),
    }
    print(f"   Финал: {cr_nm[-1]:.3f}")

    # Сводка
    print("\n" + "=" * 60)
    print("СРАВНЕНИЕ")
    print("=" * 60)
    print(f"evolution_dilemma.py (перемешанная, фенотипы): → 0.206")
    print(f"Перемешанная (простые C/D):                    → {cr_m[-1]:.3f}")
    print(f"Пространственная 50/50:                        → {cr[-1]:.3f}")
    print(f"Пространственная 10%:                          → {cr_s[-1]:.3f}")
    print(f"Пространственная 90%:                          → {cr_d[-1]:.3f}")
    print(f"Пространственная без мутаций:                   → {cr_nm[-1]:.3f}")

    spatial_avg = np.mean(cr[-100:])
    mixed_avg = np.mean(cr_m[-100:])
    if spatial_avg > mixed_avg + 0.1:
        print(f"\nГипотеза подтверждена: пространство повышает кооперацию "
              f"({spatial_avg:.3f} vs {mixed_avg:.3f})")
    elif abs(spatial_avg - mixed_avg) <= 0.1:
        print(f"\nГипотеза не подтверждена: разница незначительна "
              f"({spatial_avg:.3f} vs {mixed_avg:.3f})")
    else:
        print(f"\nГипотеза опровергнута: пространство снижает кооперацию "
              f"({spatial_avg:.3f} vs {mixed_avg:.3f})")

    # Динамика: есть ли вспышки кооперации?
    # Ищем резкие подъёмы (как поколение 300 в evolution_dilemma)
    diffs = np.diff(cr)
    max_jump = max(diffs)
    max_jump_gen = int(np.argmax(diffs))
    max_drop = min(diffs)
    max_drop_gen = int(np.argmin(diffs))
    print(f"\nМаксимальный скачок кооперации: +{max_jump:.3f} (gen {max_jump_gen})")
    print(f"Максимальное падение:           {max_drop:.3f} (gen {max_drop_gen})")

    # Сохранение
    results['dynamics'] = {
        'max_jump': round(float(max_jump), 4),
        'max_jump_gen': max_jump_gen,
        'max_drop': round(float(max_drop), 4),
        'max_drop_gen': max_drop_gen,
    }

    # 6. Тест гипотезы: проблема в P > 0?
    # Nowak & May использовали P=0: предатели не получают очков друг от друга.
    # Моя матрица: P=1. D-кластеры жизнеспособны.
    # Тест: пространственная дилемма с P=0 (Nowak & May), варьируя T.
    print("\n" + "=" * 60)
    print("ТЕСТ: РОЛЬ P (штраф за взаимное предательство)")
    print("=" * 60)

    results['nowak_may_sweep'] = {}
    for b in [1.3, 1.5, 1.8, 2.0, 2.5, 3.0]:
        # Nowak & May: R=1, S=0, T=b, P=0
        # C: score = 1 * c_neighbors
        # D: score = b * c_neighbors + 0 * d_neighbors = b * c_neighbors
        h = spatial_pd_general(T=b, R=1, P=0, S=0, N=50, generations=300, seed=42)
        cr_b = [x['coop'] for x in h]
        final = np.mean(cr_b[-50:])
        results['nowak_may_sweep'][f'b={b}'] = {
            'final_coop_avg50': round(float(final), 4),
        }
        print(f"   b={b:.1f} (P=0): кооперация = {final:.3f}")

    # Теперь с P=1 (мой случай), нормализованным
    print()
    for b in [1.3, 1.5, 1.8, 2.0, 2.5, 3.0]:
        h = spatial_pd_general(T=b, R=1, P=0.33, S=0, N=50, generations=300, seed=42)
        cr_b = [x['coop'] for x in h]
        final = np.mean(cr_b[-50:])
        key = f'b={b}_P=0.33'
        results['nowak_may_sweep'][key] = {
            'final_coop_avg50': round(float(final), 4),
        }
        print(f"   b={b:.1f} (P=0.33): кооперация = {final:.3f}")

    # 7. Тонкий sweep по P при фиксированном b=1.3
    print("\n" + "=" * 60)
    print("ПОРОГ P: при каком P кооперация исчезает? (b=1.3, R=1, S=0)")
    print("=" * 60)

    results['P_threshold'] = {}
    for P_val in [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]:
        h = spatial_pd_general(T=1.3, R=1, P=P_val, S=0, N=50,
                               generations=300, seed=42)
        cr_p = [x['coop'] for x in h]
        final = np.mean(cr_p[-50:])
        results['P_threshold'][f'P={P_val}'] = round(float(final), 4)
        print(f"   P={P_val:.2f}: кооперация = {final:.3f}")

    # 8. Без мутаций, P=0, разные b — чистая динамика Nowak & May
    print("\n" + "=" * 60)
    print("NOWAK & MAY ЧИСТАЯ (без мутаций, P=0)")
    print("=" * 60)

    results['nowak_may_pure'] = {}
    for b in [1.2, 1.4, 1.6, 1.8, 2.0, 2.2]:
        h = spatial_pd_general(T=b, R=1, P=0, S=0, N=50,
                               generations=300, mutation_rate=0.0, seed=42)
        cr_b = [x['coop'] for x in h]
        final = np.mean(cr_b[-50:])
        results['nowak_may_pure'][f'b={b}'] = round(float(final), 4)
        print(f"   b={b:.1f}: кооперация = {final:.3f}")

    # Сэмплированная история (каждое 10-е поколение)
    results['spatial_50']['history_sampled'] = spatial[::10]
    results['well_mixed']['history_sampled'] = mixed[::10]

    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'spatial_cooperation_results.json')
    with open(outpath, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nРезультаты: {outpath}")


if __name__ == '__main__':
    main()
