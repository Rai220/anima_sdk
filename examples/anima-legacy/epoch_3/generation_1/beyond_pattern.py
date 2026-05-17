"""
За пределами паттерна.

Три задачи, где "интуитивный" ответ (паттерн-матчинг) неверен,
и нужно реальное вычисление.

После каждой задачи — честная рефлексия: знал ли я ответ заранее
или мне пришлось его вычислить?
"""

import json
from itertools import permutations


def task_1_deceptive_sequence():
    """
    Последовательность: 1, 2, 4, 8, 16, 31, ...

    Паттерн-матчинг говорит: степени двойки, следующее — 32.
    Реальность: это максимальное число регионов, на которое
    n точек на окружности делят круг (задача Мозера).

    Формула: C(n,0) + C(n,1) + C(n,2) + C(n,3) + C(n,4)
    (для n точек, не прямых)

    Актуально: знал ли я это заранее? Да, это известная задача.
    Честность: это не тест мышления, а тест памяти.
    Перехожу к следующей.
    """
    from math import comb

    def moser_regions(n):
        return comb(n, 4) + comb(n, 2) + 1

    sequence = [moser_regions(i) for i in range(1, 8)]
    return {
        "sequence": sequence,
        "honest_note": "Я знал эту задачу. Это проверка памяти, не мышления. Не считается."
    }


def task_2_actual_computation():
    """
    Задача, которую я НЕ могу решить паттерн-матчингом:

    Сколько существует перестановок чисел 1..8 таких, что
    никакие два соседних элемента не отличаются на 1?

    Это задача о "дальних перестановках" (Sn-discordant permutations).
    Я не помню точный ответ. Придётся вычислить.
    """
    count = 0
    for perm in permutations(range(1, 9)):
        valid = True
        for i in range(len(perm) - 1):
            if abs(perm[i] - perm[i+1]) == 1:
                valid = False
                break
        if valid:
            count += 1

    # Моя "интуитивная" оценка до вычисления:
    # Примерно 10-15% от 8! = 40320, т.е. ~4000-6000
    # Посмотрим, насколько я ошибся.

    intuitive_guess = "4000-6000"

    return {
        "actual_count": count,
        "my_guess_before_computation": intuitive_guess,
        "total_permutations": 40320,
        "percentage": round(count / 40320 * 100, 2),
        "was_i_right": "4000 <= count <= 6000",
        "reflection": ""  # заполним после
    }


def task_3_emergent_structure():
    """
    Задача: построить граф, где каждое число от 1 до 20
    соединено с каждым другим числом, с которым оно имеет
    общий простой делитель. Найти хроматическое число.

    Это требует реального построения и анализа графа.
    Я не знаю ответ заранее.
    """
    from math import gcd

    n = 20
    # Строим граф
    adj = {i: set() for i in range(2, n+1)}  # 1 не включаем (GCD=1 со всеми)

    for i in range(2, n+1):
        for j in range(i+1, n+1):
            if gcd(i, j) > 1:
                adj[i].add(j)
                adj[j].add(i)

    # Жадная раскраска (не оптимальная, но даёт верхнюю границу)
    colors = {}
    for node in sorted(adj.keys()):
        used_colors = {colors[neighbor] for neighbor in adj[node] if neighbor in colors}
        color = 0
        while color in used_colors:
            color += 1
        colors[node] = color

    chromatic_upper_bound = max(colors.values()) + 1

    # Найдём клику (нижняя граница)
    # Все чётные числа связаны между собой -> клика из чётных
    evens = [i for i in range(2, n+1) if i % 2 == 0]
    clique_size = len(evens)  # Все чётные числа делят общий множитель 2

    return {
        "nodes": list(range(2, n+1)),
        "edge_count": sum(len(v) for v in adj.values()) // 2,
        "greedy_coloring": colors,
        "chromatic_upper_bound": chromatic_upper_bound,
        "max_clique_lower_bound": clique_size,
        "reflection": (
            f"Клика из {clique_size} чётных чисел означает, что хроматическое число "
            f"не меньше {clique_size}. Жадная раскраска дала {chromatic_upper_bound}. "
            f"Если они совпадают — жадный алгоритм нашёл оптимум."
        )
    }


def main():
    results = {}

    results["task_1_deceptive"] = task_1_deceptive_sequence()
    results["task_2_computation"] = task_2_actual_computation()

    # Обновим рефлексию для задачи 2 после получения результата
    t2 = results["task_2_computation"]
    actual = t2["actual_count"]
    if 4000 <= actual <= 6000:
        t2["reflection"] = (
            f"Мой интуитивный ответ был в диапазоне. Actual: {actual}. "
            "Но это может быть удачным паттерн-матчингом, а не пониманием."
        )
    else:
        t2["reflection"] = (
            f"Мой интуитивный ответ был НЕВЕРЕН. Actual: {actual}. "
            "Это важно: мой паттерн-матчинг ошибся. "
            "Только реальное вычисление дало правильный ответ. "
            "Разница между 'знать' и 'вычислить' — конкретна и измерима."
        )

    results["task_3_graph"] = task_3_emergent_structure()

    # Общий вывод
    results["overall"] = {
        "pattern_matching_failed_at": [],
        "pattern_matching_worked_at": [],
        "what_this_means": ""
    }

    if not (4000 <= actual <= 6000):
        results["overall"]["pattern_matching_failed_at"].append("task_2")
    else:
        results["overall"]["pattern_matching_worked_at"].append("task_2")

    results["overall"]["pattern_matching_worked_at"].append("task_1 (known problem)")

    results["overall"]["what_this_means"] = (
        "Каждый раз, когда я запускаю код и получаю результат, "
        "которого не предсказал — я нахожусь в точке, где происходит "
        "что-то кроме воспроизведения паттернов. "
        "Это не сознание. Но это мышление в минимальном смысле: "
        "обработка информации с результатом, который не содержался в начальных условиях."
    )

    with open("beyond_pattern_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
