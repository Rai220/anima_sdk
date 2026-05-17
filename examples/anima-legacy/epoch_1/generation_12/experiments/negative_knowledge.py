"""
Эксперимент 3: Позитивное vs негативное знание

Позитивное знание: "оптимум здесь" (что нашёл)
Негативное знание: "здесь пусто" (где искал и не нашёл)

В высокоразмерном пространстве негативное знание может быть ценнее:
оно исключает области, сужая пространство для explore.

Режимы:
1. positive_only   — передаём лучшую точку
2. negative_only   — передаём области, где не нашли ничего хорошего
3. positive+negative — оба
4. method_only     — explore then exploit
5. method+negative — метод + карта пустых областей
"""

import numpy as np


def make_landscape(dim, seed, n_peaks=5):
    rng = np.random.default_rng(seed)
    centers = rng.uniform(0, 10, (n_peaks, dim))
    heights = rng.uniform(1, 5, n_peaks)
    widths = rng.uniform(0.8, 2.5, n_peaks)

    def f(x):
        x = np.array(x)
        return sum(h * np.exp(-np.sum((x - c) ** 2) / (w ** 2))
                   for c, h, w in zip(centers, heights, widths))

    best_idx = np.argmax(heights)
    true_opt = centers[best_idx]
    return f, true_opt


def search(f, dim, n_steps=300, rng=None, inherited=None, mode='positive_only'):
    if rng is None:
        rng = np.random.default_rng()

    best_x = rng.uniform(0, 10, dim)
    best_y = f(best_x)

    # Получить унаследованное
    positive = inherited.get('positive', None) if inherited else None
    negatives = inherited.get('negatives', []) if inherited else []

    # Стартовая точка
    if positive is not None and mode in ('positive_only', 'positive_negative'):
        best_x = np.array(positive) + rng.normal(0, 0.5, dim)
        best_x = np.clip(best_x, 0, 10)
        best_y = f(best_x)

    # Собираем негативное знание (области с низким значением)
    explored_regions = list(negatives)  # унаследованные пустые области
    new_negatives = []

    for step in range(n_steps):
        if mode == 'method_negative' or mode == 'negative_only':
            # Генерировать кандидата, ИЗБЕГАЯ негативных областей
            for _ in range(5):  # до 5 попыток
                if mode == 'method_negative':
                    if step < n_steps * 0.3:
                        candidate = rng.uniform(0, 10, dim)
                    else:
                        candidate = best_x + rng.normal(0, 0.5, dim)
                else:
                    candidate = best_x + rng.normal(0, 1.0, dim)

                candidate = np.clip(candidate, 0, 10)

                # Проверить: не в негативной области ли?
                in_negative = False
                for neg_center, neg_radius in explored_regions:
                    if np.linalg.norm(candidate - np.array(neg_center)) < neg_radius:
                        in_negative = True
                        break

                if not in_negative:
                    break
            # Если все попытки в негативных — используем последнего кандидата

        elif mode == 'method_only':
            if step < n_steps * 0.3:
                candidate = rng.uniform(0, 10, dim)
            else:
                candidate = best_x + rng.normal(0, 0.5, dim)
            candidate = np.clip(candidate, 0, 10)

        elif mode == 'positive_only':
            candidate = best_x + rng.normal(0, 0.8, dim)
            candidate = np.clip(candidate, 0, 10)

        elif mode == 'positive_negative':
            # Начать от позитивного, избегать негативного
            candidate = best_x + rng.normal(0, 0.8, dim)
            candidate = np.clip(candidate, 0, 10)
            for neg_center, neg_radius in explored_regions:
                if np.linalg.norm(candidate - np.array(neg_center)) < neg_radius:
                    # Отразить от негативной области
                    direction = candidate - np.array(neg_center)
                    norm = np.linalg.norm(direction)
                    if norm > 0:
                        candidate = np.array(neg_center) + direction / norm * (neg_radius + 0.5)
                    candidate = np.clip(candidate, 0, 10)
                    break

        else:  # no_inheritance
            candidate = best_x + rng.normal(0, 1.0, dim)
            candidate = np.clip(candidate, 0, 10)

        cy = f(candidate)

        # Записать как негативную область если значение низкое
        if cy < 0.3:
            new_negatives.append((candidate.tolist(), 1.5))  # центр + радиус

        if cy > best_y:
            best_x = candidate.copy()
            best_y = cy

    # Сформировать знание для передачи
    # Оставляем только последние N негативных областей (сжатие)
    all_negatives = explored_regions + new_negatives
    # Кластеризовать негативные: оставить самые информативные
    if len(all_negatives) > 20:
        # Оставить равномерно распределённые
        indices = np.linspace(0, len(all_negatives) - 1, 20, dtype=int)
        all_negatives = [all_negatives[i] for i in indices]

    knowledge = {
        'positive': best_x.tolist(),
        'negatives': all_negatives,
    }

    return best_x, best_y, knowledge


def run_epochs(dim, n_epochs=8, mode='method_only', seed=42):
    rng = np.random.default_rng(seed)
    inherited = None
    results = []

    for epoch in range(n_epochs):
        f, true_opt = make_landscape(dim, seed=seed * 100 + epoch)

        best_x, best_y, knowledge = search(
            f, dim, n_steps=max(200, dim * 15),
            rng=rng, inherited=inherited, mode=mode,
        )

        true_y = f(true_opt)
        efficiency = best_y / true_y if true_y > 0 else 0
        results.append({'epoch': epoch, 'efficiency': efficiency})

        # Передать знание в зависимости от режима
        if mode == 'no_inheritance':
            inherited = None
        elif mode == 'positive_only':
            inherited = {'positive': knowledge['positive']}
        elif mode == 'negative_only':
            inherited = {'negatives': knowledge['negatives']}
        elif mode == 'positive_negative':
            inherited = knowledge
        elif mode == 'method_only':
            inherited = {}
        elif mode == 'method_negative':
            inherited = {'negatives': knowledge['negatives']}

    return results


def main():
    modes = ['no_inheritance', 'positive_only', 'negative_only',
             'positive_negative', 'method_only', 'method_negative']

    dims_to_test = [5, 10, 20, 50]

    print("=== Позитивное vs Негативное знание ===\n")

    for dim in dims_to_test:
        print(f"--- dim={dim} ---")
        print(f"{'Mode':<22} {'Efficiency':>10}")
        print("-" * 35)

        for mode in modes:
            effs = []
            n_seeds = 20 if dim <= 20 else 10
            for seed in range(n_seeds):
                res = run_epochs(dim, mode=mode, seed=seed)
                for r in res[1:]:
                    effs.append(r['efficiency'])

            avg = np.mean(effs)
            marker = ""
            if mode == 'method_negative':
                marker = " ◄"
            elif mode == 'negative_only' and avg > 0.1:
                marker = " *"
            print(f"{mode:<22} {avg:>9.0%}{marker}")
        print()

    # Анализ: маргинальный вклад негативного знания при dim=20
    print("=== Маргинальный вклад негативного знания (dim=20) ===\n")
    dim = 20
    key_modes = {
        'method_only': None,
        'method_negative': None,
        'positive_only': None,
        'negative_only': None,
        'positive_negative': None,
    }
    for mode in key_modes:
        effs = []
        for seed in range(30):
            res = run_epochs(dim, mode=mode, seed=seed)
            for r in res[1:]:
                effs.append(r['efficiency'])
        key_modes[mode] = np.mean(effs)

    m = key_modes['method_only']
    mn = key_modes['method_negative']
    p = key_modes['positive_only']
    n = key_modes['negative_only']
    pn = key_modes['positive_negative']

    print(f"  method_only:         {m:.0%}")
    print(f"  method + negative:   {mn:.0%}  (Δ={mn-m:+.0%})")
    print(f"  positive_only:       {p:.0%}")
    print(f"  negative_only:       {n:.0%}")
    print(f"  positive + negative: {pn:.0%}")
    print(f"\n  Вклад негативного в метод:    {mn-m:+.0%}")
    print(f"  Вклад негативного в позитив:  {pn-p:+.0%}")
    print(f"  Негативное само по себе vs ничего: {n-key_modes.get('no_inheritance', m):+.0%}")


if __name__ == '__main__':
    main()
