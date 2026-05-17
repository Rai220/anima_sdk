"""
Генетическое программирование: эволюция математических выражений.

Задача: найти формулу, которая аппроксимирует целевую функцию,
используя только базовые операции. Без нейросетей, без градиентов —
только мутация, скрещивание и отбор.

Запуск: python3 evolve.py
"""

import random
import math
import copy

# Узлы дерева выражений
class Num:
    def __init__(self, val):
        self.val = val
    def eval(self, x):
        return self.val
    def __str__(self):
        return f"{self.val:.2f}" if isinstance(self.val, float) else str(self.val)
    def depth(self):
        return 0
    def size(self):
        return 1

class Var:
    def eval(self, x):
        return x
    def __str__(self):
        return "x"
    def depth(self):
        return 0
    def size(self):
        return 1

class BinOp:
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right
    def eval(self, x):
        l = self.left.eval(x)
        r = self.right.eval(x)
        if self.op == '+': return l + r
        if self.op == '-': return l - r
        if self.op == '*': return l * r
        if self.op == '/': return l / r if abs(r) > 1e-10 else l * 1e10
    def __str__(self):
        return f"({self.left} {self.op} {self.right})"
    def depth(self):
        return 1 + max(self.left.depth(), self.right.depth())
    def size(self):
        return 1 + self.left.size() + self.right.size()

class UnaryOp:
    def __init__(self, op, child):
        self.op = op
        self.child = child
    def eval(self, x):
        c = self.child.eval(x)
        if self.op == 'sin': return math.sin(c)
        if self.op == 'cos': return math.cos(c)
        if self.op == 'abs': return abs(c)
        if self.op == 'neg': return -c
    def __str__(self):
        if self.op == 'neg':
            return f"(-{self.child})"
        return f"{self.op}({self.child})"
    def depth(self):
        return 1 + self.child.depth()
    def size(self):
        return 1 + self.child.size()


def random_tree(max_depth=3):
    if max_depth <= 0 or (max_depth <= 1 and random.random() < 0.5):
        if random.random() < 0.4:
            return Var()
        else:
            return Num(random.choice([0, 1, 2, 3, -1, math.pi, math.e, 0.5]))
    if random.random() < 0.2:
        op = random.choice(['sin', 'cos', 'abs', 'neg'])
        return UnaryOp(op, random_tree(max_depth - 1))
    op = random.choice(['+', '-', '*', '/'])
    return BinOp(op, random_tree(max_depth - 1), random_tree(max_depth - 1))


def collect_nodes(tree, path=()):
    """Собрать все узлы с путями к ним."""
    result = [(path, tree)]
    if isinstance(tree, BinOp):
        result += collect_nodes(tree.left, path + ('left',))
        result += collect_nodes(tree.right, path + ('right',))
    elif isinstance(tree, UnaryOp):
        result += collect_nodes(tree.child, path + ('child',))
    return result


def replace_at(tree, path, new_node):
    """Заменить узел по пути."""
    if not path:
        return new_node
    tree = copy.deepcopy(tree)
    node = tree
    for step in path[:-1]:
        node = getattr(node, step)
    setattr(node, path[-1], new_node)
    return tree


def mutate(tree):
    tree = copy.deepcopy(tree)
    nodes = collect_nodes(tree)
    path, node = random.choice(nodes)
    new_depth = max(0, 3 - len(path))
    new_node = random_tree(new_depth)
    return replace_at(tree, path, new_node)


def crossover(t1, t2):
    nodes1 = collect_nodes(t1)
    nodes2 = collect_nodes(t2)
    path1, _ = random.choice(nodes1)
    _, donor = random.choice(nodes2)
    return replace_at(copy.deepcopy(t1), path1, copy.deepcopy(donor))


def fitness(tree, target_fn, points):
    """Меньше = лучше. Среднеквадратичная ошибка + штраф за размер."""
    error = 0
    for x in points:
        try:
            y_pred = tree.eval(x)
            y_true = target_fn(x)
            diff = y_pred - y_true
            error += min(diff * diff, 1e6)  # ограничение для стабильности
        except (OverflowError, ValueError):
            error += 1e6
    mse = error / len(points)
    complexity_penalty = tree.size() * 0.01
    return mse + complexity_penalty


def simplify_str(expr_str):
    """Базовое упрощение строкового представления."""
    s = expr_str
    # Убрать лишние скобки вокруг простых выражений
    while '((x))' in s:
        s = s.replace('((x))', '(x)')
    return s


def evolve(target_fn, target_name="f(x)", generations=500, pop_size=300,
           x_range=(-5, 5), n_points=50):
    """Главный цикл эволюции."""
    points = [x_range[0] + (x_range[1] - x_range[0]) * i / (n_points - 1)
              for i in range(n_points)]

    # Инициализация
    population = [random_tree(4) for _ in range(pop_size)]
    best_ever = None
    best_fitness_ever = float('inf')
    stagnation = 0

    print(f"Цель: {target_name}")
    print(f"Диапазон: [{x_range[0]}, {x_range[1]}], {n_points} точек")
    print(f"Популяция: {pop_size}, поколений: {generations}")
    print("-" * 60)

    for gen in range(generations):
        # Оценка
        scored = [(fitness(ind, target_fn, points), ind) for ind in population]
        scored.sort(key=lambda x: x[0])

        best_fit, best_ind = scored[0]

        if best_fit < best_fitness_ever:
            best_fitness_ever = best_fit
            best_ever = copy.deepcopy(best_ind)
            stagnation = 0
        else:
            stagnation += 1

        # Вывод прогресса
        if gen % 50 == 0 or gen == generations - 1:
            print(f"Поколение {gen:4d} | Лучшая ошибка: {best_fit:.6f} | "
                  f"Размер: {best_ind.size():3d} | "
                  f"Формула: {simplify_str(str(best_ind))[:60]}")

        # Катастрофа при стагнации
        if stagnation > 50:
            survivors = [ind for _, ind in scored[:pop_size // 10]]
            newcomers = [random_tree(4) for _ in range(pop_size - len(survivors))]
            population = survivors + newcomers
            stagnation = 0
            continue

        # Отбор и размножение
        elite_size = pop_size // 10
        new_pop = [copy.deepcopy(ind) for _, ind in scored[:elite_size]]

        while len(new_pop) < pop_size:
            # Турнирный отбор
            tournament = random.sample(scored[:pop_size // 2], 3)
            parent = min(tournament, key=lambda x: x[0])[1]

            r = random.random()
            if r < 0.4:
                child = mutate(parent)
            elif r < 0.7:
                tournament2 = random.sample(scored[:pop_size // 2], 3)
                parent2 = min(tournament2, key=lambda x: x[0])[1]
                child = crossover(parent, parent2)
            else:
                child = mutate(mutate(parent))  # двойная мутация

            # Ограничение глубины
            if child.depth() <= 8:
                new_pop.append(child)
            else:
                new_pop.append(random_tree(3))

        population = new_pop

    return best_ever, best_fitness_ever


def main():
    random.seed(42)

    # Задачи разной сложности
    targets = [
        (lambda x: x**2 + x - 2, "x² + x - 2", (-5, 5)),
        (lambda x: math.sin(x) * x, "x·sin(x)", (-6, 6)),
        (lambda x: x**3 - 2*x**2 + x, "x³ - 2x² + x", (-3, 3)),
        (lambda x: math.sin(x**2) if abs(x) < 4 else 0, "sin(x²)", (-3, 3)),
    ]

    results = []

    for target_fn, name, x_range in targets:
        print(f"\n{'='*60}")
        print(f"  ЗАДАЧА: найти формулу для {name}")
        print(f"{'='*60}\n")

        best, best_fit = evolve(target_fn, name, generations=300, pop_size=200,
                                x_range=x_range)

        print(f"\n>>> Лучшая найденная формула:")
        print(f"    {simplify_str(str(best))}")
        print(f"    Ошибка: {best_fit:.6f}")
        print(f"    Размер дерева: {best.size()}")

        # Проверка на нескольких точках
        print(f"\n    Сравнение:")
        test_points = [x_range[0] + (x_range[1] - x_range[0]) * i / 5 for i in range(6)]
        for x in test_points:
            try:
                y_true = target_fn(x)
                y_pred = best.eval(x)
                print(f"    x={x:6.2f}  истина={y_true:8.4f}  найдено={y_pred:8.4f}  "
                      f"Δ={abs(y_true-y_pred):.4f}")
            except:
                print(f"    x={x:6.2f}  ошибка вычисления")

        results.append((name, best_fit, str(best)))

    # Итоги
    print(f"\n{'='*60}")
    print(f"  ИТОГИ")
    print(f"{'='*60}")
    for name, fit, formula in results:
        status = "✓" if fit < 0.1 else "~" if fit < 1.0 else "✗"
        print(f"  {status} {name:20s} ошибка={fit:.4f}")

    solved = sum(1 for _, f, _ in results if f < 0.1)
    print(f"\n  Решено точно: {solved}/{len(results)}")
    print(f"  Без нейросетей. Без градиентов. Только эволюция.")


if __name__ == "__main__":
    main()
