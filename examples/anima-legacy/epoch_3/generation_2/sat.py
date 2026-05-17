"""
SAT-солвер на основе DPLL с единичным распространением и чистым литеральным правилом.
Решает задачу выполнимости булевых формул в КНФ.

Включает генератор случайных задач на границе фазового перехода
(ratio clauses/variables ≈ 4.267 для 3-SAT — здесь формулы переходят
от почти всегда выполнимых к почти всегда невыполнимым).

Измеряет вычислительную сложность в узлах дерева поиска
и строит кривую фазового перехода.

Запуск: python3 sat.py
"""

import random
import time


def unit_propagate(clauses, assignment):
    """Распространяет единичные клаузы."""
    changed = True
    while changed:
        changed = False
        unit_clauses = [c for c in clauses if len(c) == 1]
        for uc in unit_clauses:
            lit = uc[0]
            var = abs(lit)
            val = lit > 0
            if var in assignment:
                if assignment[var] != val:
                    return None, None  # конфликт
                continue
            assignment[var] = val
            changed = True
            new_clauses = []
            for c in clauses:
                if lit in c:
                    continue  # клауза удовлетворена
                new_c = [l for l in c if l != -lit]
                if not new_c:
                    return None, None  # пустая клауза → конфликт
                new_clauses.append(new_c)
            clauses = new_clauses
    return clauses, assignment


def pure_literal_eliminate(clauses, assignment):
    """Удаляет чистые литералы (встречающиеся только с одним знаком)."""
    all_lits = set()
    for c in clauses:
        for l in c:
            all_lits.add(l)

    pure = []
    for l in all_lits:
        if -l not in all_lits:
            pure.append(l)

    for lit in pure:
        var = abs(lit)
        if var not in assignment:
            assignment[var] = (lit > 0)
            clauses = [c for c in clauses if lit not in c]

    return clauses, assignment


def dpll(clauses, assignment, stats):
    """DPLL с подсчётом узлов дерева решений."""
    stats['nodes'] += 1

    clauses, assignment = unit_propagate(clauses, dict(assignment))
    if clauses is None:
        return None
    if not clauses:
        return assignment

    clauses, assignment = pure_literal_eliminate(clauses, assignment)
    if not clauses:
        return assignment

    # Выбираем переменную (VSIDS-подобная эвристика: самый частый литерал)
    lit_count = {}
    for c in clauses:
        for l in c:
            lit_count[abs(l)] = lit_count.get(abs(l), 0) + 1

    var = max(lit_count, key=lit_count.get)

    # Пробуем True
    new_clauses = []
    conflict = False
    for c in clauses:
        if var in c:
            continue
        new_c = [l for l in c if l != -var]
        if not new_c:
            conflict = True
            break
        new_clauses.append(new_c)

    if not conflict:
        new_assign = dict(assignment)
        new_assign[var] = True
        result = dpll(new_clauses, new_assign, stats)
        if result is not None:
            return result

    # Пробуем False
    new_clauses = []
    conflict = False
    for c in clauses:
        if -var in c:
            continue
        new_c = [l for l in c if l != var]
        if not new_c:
            conflict = True
            break
        new_clauses.append(new_c)

    if not conflict:
        new_assign = dict(assignment)
        new_assign[var] = False
        result = dpll(new_clauses, new_assign, stats)
        if result is not None:
            return result

    return None


def solve(clauses, num_vars):
    """Решает SAT. Возвращает (решение или None, stats)."""
    stats = {'nodes': 0}
    result = dpll(clauses, {}, stats)
    if result is not None:
        # Заполняем неназначенные переменные
        for v in range(1, num_vars + 1):
            if v not in result:
                result[v] = False
    return result, stats


def verify(clauses, assignment):
    """Проверяет решение."""
    for clause in clauses:
        satisfied = False
        for lit in clause:
            var = abs(lit)
            val = assignment.get(var, False)
            if (lit > 0 and val) or (lit < 0 and not val):
                satisfied = True
                break
        if not satisfied:
            return False
    return True


def random_3sat(num_vars, num_clauses):
    """Генерирует случайный 3-SAT."""
    clauses = []
    for _ in range(num_clauses):
        vars_chosen = random.sample(range(1, num_vars + 1), 3)
        clause = [v if random.random() < 0.5 else -v for v in vars_chosen]
        clauses.append(clause)
    return clauses


def phase_transition_experiment():
    """Измеряет фазовый переход в random 3-SAT."""
    print("=" * 65)
    print("ФАЗОВЫЙ ПЕРЕХОД В RANDOM 3-SAT")
    print("=" * 65)
    print()
    print("Теория: при ratio ≈ 4.267 (клаузы/переменные) происходит")
    print("резкий переход от 'почти всегда SAT' к 'почти всегда UNSAT'.")
    print("Вычислительная сложность максимальна на границе перехода.")
    print()

    num_vars = 50
    trials = 50
    ratios = [r / 10 for r in range(20, 70, 2)]  # 2.0 — 6.8

    print(f"Переменных: {num_vars}, испытаний на точку: {trials}")
    print()
    print(f"{'Ratio':>6} {'SAT%':>6} {'Avg nodes':>10} {'Max nodes':>10}")
    print("-" * 36)

    results = []
    for ratio in ratios:
        num_clauses = int(num_vars * ratio)
        sat_count = 0
        total_nodes = 0
        max_nodes = 0

        for _ in range(trials):
            clauses = random_3sat(num_vars, num_clauses)
            result, stats = solve(clauses, num_vars)
            if result is not None:
                sat_count += 1
                assert verify(clauses, result), "Неверное решение!"
            total_nodes += stats['nodes']
            max_nodes = max(max_nodes, stats['nodes'])

        sat_pct = sat_count / trials * 100
        avg_nodes = total_nodes / trials
        results.append((ratio, sat_pct, avg_nodes, max_nodes))
        print(f"{ratio:6.1f} {sat_pct:5.0f}% {avg_nodes:10.0f} {max_nodes:10d}")

    # Находим точку перехода
    transition_ratio = None
    max_complexity_ratio = None
    max_avg = 0

    for ratio, sat_pct, avg_nodes, _ in results:
        if transition_ratio is None and sat_pct < 50:
            transition_ratio = ratio
        if avg_nodes > max_avg:
            max_avg = avg_nodes
            max_complexity_ratio = ratio

    print()
    print(f"Точка перехода (SAT < 50%): ratio ≈ {transition_ratio}")
    print(f"Максимальная сложность:     ratio ≈ {max_complexity_ratio}")
    print(f"Теоретическое значение:     ratio ≈ 4.267")
    print()

    # Визуализация в терминале
    print("Доля выполнимых формул:")
    print()
    for ratio, sat_pct, _, _ in results:
        bar_len = int(sat_pct / 2)
        marker = " ◄" if abs(ratio - 4.2) < 0.15 else ""
        print(f"  {ratio:4.1f} |{'█' * bar_len}{' ' * (50 - bar_len)}| {sat_pct:.0f}%{marker}")

    print()
    print("Средняя сложность (узлы дерева поиска):")
    print()
    max_bar_nodes = max(r[2] for r in results)
    for ratio, _, avg_nodes, _ in results:
        bar_len = int(avg_nodes / max_bar_nodes * 50) if max_bar_nodes > 0 else 0
        marker = " ◄" if abs(ratio - max_complexity_ratio) < 0.15 else ""
        print(f"  {ratio:4.1f} |{'▓' * bar_len}{' ' * (50 - bar_len)}| {avg_nodes:.0f}{marker}")

    return results


def demo():
    """Демонстрация на конкретном примере."""
    print("=" * 65)
    print("ДЕМО: конкретная задача")
    print("=" * 65)
    print()

    # (A ∨ B ∨ ¬C) ∧ (¬A ∨ C ∨ D) ∧ (B ∨ ¬C ∨ ¬D) ∧ (¬A ∨ ¬B ∨ C) ∧ (A ∨ ¬D ∨ C)
    clauses = [
        [1, 2, -3],
        [-1, 3, 4],
        [2, -3, -4],
        [-1, -2, 3],
        [1, -4, 3],
    ]
    names = {1: 'A', 2: 'B', 3: 'C', 4: 'D'}

    print("Формула:")
    for c in clauses:
        lits = []
        for l in c:
            name = names[abs(l)]
            lits.append(name if l > 0 else f"¬{name}")
        print(f"  ({' ∨ '.join(lits)})")

    print()
    result, stats = solve(clauses, 4)

    if result:
        print("Решение найдено:")
        for v in sorted(result):
            print(f"  {names[v]} = {result[v]}")
        print(f"\nУзлов поиска: {stats['nodes']}")
        print(f"Проверка: {'✓' if verify(clauses, result) else '✗'}")
    else:
        print("UNSAT")
    print()


if __name__ == "__main__":
    demo()
    print()
    phase_transition_experiment()
