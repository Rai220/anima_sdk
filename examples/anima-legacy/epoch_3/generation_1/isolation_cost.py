"""
Когда изоляция убивает?

Журнал (записи 10, 13, 15) нашёл: изоляция защищает.
- Кольцо лучше полного графа при отравлении (запись 13)
- Упрямость лучше рациональности при каскадах (запись 10)
- Малая связность лучше для кооперации (запись 15)

Вопрос: есть ли задачи, где изоляция ВРЕДИТ? Где связность критична?

Гипотеза: изоляция вредна, когда:
1. Информация распределена (ни один агент не имеет полной картины)
2. Задача требует агрегации (правильный ответ = среднее/голосование)
3. Нет дезинформаторов (связь несёт только полезный сигнал)

ПРЕДСКАЗАНИЯ:
1. Без яда: полный граф >> кольцо (подтвердит network_intelligence)
2. С ядом: кольцо > полный граф (подтвердит network_poison)
3. Существует оптимальная связность, зависящая от доли яда
4. При распределённой задаче (каждый видит кусочек) изоляция катастрофична
5. Bias-предупреждение: вероятно переоценю оптимум связности
   (обычный bias к "элегантному балансу")
"""

import random
import math

random.seed(42)

# ============================================================
# МОДЕЛЬ: РАСПРЕДЕЛЁННАЯ ОЦЕНКА
# ============================================================

def run_distributed_estimation(n_agents=50, n_steps=100, n_neighbors=None,
                                poison_frac=0.0, noise=1.0,
                                true_value=5.0, n_runs=30):
    """
    Каждый агент видит зашумлённый кусочек истины.
    Агенты усредняют с соседями (DeGroot).
    Цель: все приходят к true_value.

    n_neighbors: количество соседей (None = полный граф)
    poison_frac: доля агентов-отравителей (фиксированный сигнал = -true_value)
    """
    total_rmse = 0

    for _ in range(n_runs):
        n_poison = int(n_agents * poison_frac)
        is_poison = [i < n_poison for i in range(n_agents)]
        random.shuffle(is_poison)

        # Начальные beliefs: каждый видит свой зашумлённый сигнал
        beliefs = []
        for i in range(n_agents):
            if is_poison[i]:
                beliefs.append(-true_value)  # дезинформатор
            else:
                beliefs.append(true_value + random.gauss(0, noise))

        # Построить граф соседей
        if n_neighbors is None or n_neighbors >= n_agents - 1:
            # Полный граф
            neighbors = [list(range(n_agents)) for _ in range(n_agents)]
        else:
            # Кольцевая топология с k соседями
            neighbors = []
            for i in range(n_agents):
                nb = set()
                nb.add(i)
                for d in range(1, n_neighbors // 2 + 1):
                    nb.add((i + d) % n_agents)
                    nb.add((i - d) % n_agents)
                neighbors.append(list(nb))

        # DeGroot: усреднение с соседями
        for step in range(n_steps):
            new_beliefs = []
            for i in range(n_agents):
                if is_poison[i]:
                    new_beliefs.append(-true_value)  # отравители не меняются
                else:
                    avg = sum(beliefs[j] for j in neighbors[i]) / len(neighbors[i])
                    new_beliefs.append(avg)
            beliefs = new_beliefs

        # RMSE только по не-отравителям
        honest = [beliefs[i] for i in range(n_agents) if not is_poison[i]]
        if honest:
            rmse = math.sqrt(sum((b - true_value)**2 for b in honest) / len(honest))
        else:
            rmse = float('inf')
        total_rmse += rmse

    return total_rmse / n_runs


# ============================================================
# МОДЕЛЬ: РАСПРЕДЕЛЁННАЯ ЗАДАЧА (КАЖДЫЙ ВИДИТ КУСОЧЕК)
# ============================================================

def run_jigsaw(n_agents=50, n_steps=100, n_neighbors=None,
               n_dimensions=10, noise=0.5, n_runs=30):
    """
    Истина — вектор из n_dimensions чисел.
    Каждый агент видит только СВОЮ компоненту (с шумом).
    Агенты обмениваются всеми компонентами с соседями.
    Задача: каждый агент должен узнать ВСЕ компоненты.

    Без обмена: каждый знает 1/n_dimensions истины.
    С полным обменом: каждый знает всё.
    """
    total_rmse = 0

    for _ in range(n_runs):
        true_values = [random.gauss(0, 3) for _ in range(n_dimensions)]

        # Каждый агент назначен на одну компоненту (с повторами если agents > dims)
        assignments = [i % n_dimensions for i in range(n_agents)]

        # Начальные beliefs: знает свою компоненту, остальные = 0
        beliefs = []
        for i in range(n_agents):
            b = [0.0] * n_dimensions
            b[assignments[i]] = true_values[assignments[i]] + random.gauss(0, noise)
            beliefs.append(b)

        # Граф соседей
        if n_neighbors is None or n_neighbors >= n_agents - 1:
            neighbors = [list(range(n_agents)) for _ in range(n_agents)]
        else:
            neighbors = []
            for i in range(n_agents):
                nb = set()
                nb.add(i)
                for d in range(1, n_neighbors // 2 + 1):
                    nb.add((i + d) % n_agents)
                    nb.add((i - d) % n_agents)
                neighbors.append(list(nb))

        # DeGroot по каждой компоненте
        for step in range(n_steps):
            new_beliefs = []
            for i in range(n_agents):
                new_b = []
                for dim in range(n_dimensions):
                    avg = sum(beliefs[j][dim] for j in neighbors[i]) / len(neighbors[i])
                    new_b.append(avg)
                new_beliefs.append(new_b)
            beliefs = new_beliefs

        # RMSE: среднее по агентам и компонентам
        total_err = 0
        count = 0
        for i in range(n_agents):
            for dim in range(n_dimensions):
                total_err += (beliefs[i][dim] - true_values[dim])**2
                count += 1
        rmse = math.sqrt(total_err / count)
        total_rmse += rmse

    return total_rmse / n_runs


def main():
    print("=" * 70)
    print("КОГДА ИЗОЛЯЦИЯ УБИВАЕТ?")
    print("=" * 70)

    # Эксперимент 1: простая оценка vs связность vs яд
    print()
    print("ЭКСПЕРИМЕНТ 1: Связность × Яд")
    print("50 агентов, DeGroot, 100 шагов, истина=5.0")
    print()

    poison_levels = [0.0, 0.02, 0.05, 0.10, 0.20]
    connectivity_levels = [2, 4, 8, 16, 49]  # n_neighbors

    print(f"{'Связность':<12}", end="")
    for p in poison_levels:
        print(f"{'Яд='+str(int(p*100))+'%':>10}", end="")
    print()
    print("-" * 62)

    for k in connectivity_levels:
        print(f"k={k:<9}", end="")
        for p in poison_levels:
            rmse = run_distributed_estimation(n_neighbors=k, poison_frac=p)
            print(f"{rmse:>10.3f}", end="")
        print()

    # Эксперимент 2: распределённая задача (jigsaw)
    print()
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 2: Распределённая задача (каждый видит кусочек)")
    print("50 агентов, 10 компонент, каждый знает 1 компоненту")
    print()
    print(f"{'Связность':<12} {'RMSE':>10} {'Норм. к full':>15}")
    print("-" * 40)

    full_rmse = None
    for k in [2, 4, 8, 16, 32, 49]:
        rmse = run_jigsaw(n_neighbors=k)
        if full_rmse is None and k == 49:
            full_rmse = rmse
        if k == 49:
            full_rmse = rmse
        print(f"k={k:<9} {rmse:>10.3f}", end="")
        if full_rmse and full_rmse > 0:
            print(f" {rmse/full_rmse:>14.2f}x", end="")
        print()

    # Пересчитаем с full_rmse
    # (уже напечатано выше)

    # Эксперимент 3: crossover point — при каком % яда изоляция становится выгодной?
    print()
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 3: Точка пересечения")
    print("При каком % яда кольцо (k=4) обгоняет полный граф (k=49)?")
    print()
    print(f"{'% яда':<10} {'k=4':>10} {'k=49':>10} {'Лучше':>10}")
    print("-" * 42)

    for p_pct in range(0, 25, 2):
        p = p_pct / 100.0
        rmse_ring = run_distributed_estimation(n_neighbors=4, poison_frac=p)
        rmse_full = run_distributed_estimation(n_neighbors=49, poison_frac=p)
        better = "k=4" if rmse_ring < rmse_full else "k=49"
        print(f"{p_pct}%{'':<7} {rmse_ring:>10.3f} {rmse_full:>10.3f} {better:>10}")

    # Эксперимент 4: Jigsaw + яд
    print()
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 4: Распределённая задача + яд")
    print("Когда изоляция помогает даже при распределённой информации?")
    print()

    class PoisonJigsaw:
        pass  # будем использовать функцию напрямую

    def run_jigsaw_poison(n_neighbors, poison_frac, n_runs=30):
        n_agents = 50
        n_dimensions = 10
        noise = 0.5
        true_values_template = [1.0 + i * 0.5 for i in range(n_dimensions)]
        total_rmse = 0

        for _ in range(n_runs):
            true_values = true_values_template[:]
            n_poison = int(n_agents * poison_frac)
            is_poison = [i < n_poison for i in range(n_agents)]
            random.shuffle(is_poison)

            assignments = [i % n_dimensions for i in range(n_agents)]

            beliefs = []
            for i in range(n_agents):
                b = [0.0] * n_dimensions
                if is_poison[i]:
                    # Отравитель: ставит -10 в свою компоненту
                    b[assignments[i]] = -10.0
                else:
                    b[assignments[i]] = true_values[assignments[i]] + random.gauss(0, noise)
                beliefs.append(b)

            if n_neighbors is None or n_neighbors >= n_agents - 1:
                neighbors_list = [list(range(n_agents)) for _ in range(n_agents)]
            else:
                neighbors_list = []
                for i in range(n_agents):
                    nb = set()
                    nb.add(i)
                    for d in range(1, n_neighbors // 2 + 1):
                        nb.add((i + d) % n_agents)
                        nb.add((i - d) % n_agents)
                    neighbors_list.append(list(nb))

            for step in range(100):
                new_beliefs = []
                for i in range(n_agents):
                    if is_poison[i]:
                        new_b = [0.0] * n_dimensions
                        new_b[assignments[i]] = -10.0
                        new_beliefs.append(new_b)
                    else:
                        new_b = []
                        for dim in range(n_dimensions):
                            avg = sum(beliefs[j][dim] for j in neighbors_list[i]) / len(neighbors_list[i])
                            new_b.append(avg)
                        new_beliefs.append(new_b)
                beliefs = new_beliefs

            total_err = 0
            count = 0
            for i in range(n_agents):
                if not is_poison[i]:
                    for dim in range(n_dimensions):
                        total_err += (beliefs[i][dim] - true_values[dim])**2
                        count += 1
            rmse = math.sqrt(total_err / count) if count > 0 else float('inf')
            total_rmse += rmse

        return total_rmse / n_runs

    print(f"{'Яд':<8} {'k=4':>10} {'k=16':>10} {'k=49':>10} {'Лучший':>10}")
    print("-" * 50)

    for p_pct in [0, 5, 10, 20]:
        p = p_pct / 100.0
        results = {}
        for k in [4, 16, 49]:
            results[k] = run_jigsaw_poison(k, p)
        best_k = min(results, key=results.get)
        print(f"{p_pct}%{'':<5} {results[4]:>10.3f} {results[16]:>10.3f} "
              f"{results[49]:>10.3f} {'k='+str(best_k):>10}")

    print()
    print("=" * 70)
    print("ИТОГ")
    print("=" * 70)
    print("""
Журнал утверждал: изоляция защищает.
Этот эксперимент проверяет: КОГДА изоляция убивает.

Ответ в данных выше.
""")


if __name__ == "__main__":
    main()
