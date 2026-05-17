"""
Экосистема: хищники, травоядные, трава.
Простые локальные правила → непредсказуемая глобальная динамика.

Правила:
- Трава растёт с вероятностью p на пустых клетках рядом с травой
- Травоядные едят траву, двигаются к ближайшей траве, размножаются при достаточной энергии
- Хищники едят травоядных, двигаются к ближайшей добыче, размножаются при достаточной энергии
- Все животные теряют энергию каждый ход и умирают при 0
"""

import random
import sys

WIDTH = 60
HEIGHT = 30
STEPS = 300
PRINT_EVERY = 50

# Символы
EMPTY = ' '
GRASS = '·'
PREY = 'o'
PREDATOR = 'X'

# Параметры
GRASS_GROW_PROB = 0.05
PREY_INITIAL = 50
PREDATOR_INITIAL = 4
PREY_ENERGY_START = 8
PREDATOR_ENERGY_START = 25
PREY_ENERGY_FROM_GRASS = 4
PREDATOR_ENERGY_FROM_PREY = 20
PREY_REPRODUCE_THRESHOLD = 16
PREDATOR_REPRODUCE_THRESHOLD = 40
PREY_REPRODUCE_COST = 8
PREDATOR_REPRODUCE_COST = 18
PREDATOR_ENERGY_COST_PER_STEP = 2  # хищники "дорогие"


class Entity:
    def __init__(self, x, y, energy):
        self.x = x
        self.y = y
        self.energy = energy
        self.alive = True


def neighbors(x, y):
    """Соседи в пределах сетки (8 направлений)."""
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                yield nx, ny


def init_world():
    """Создать начальный мир."""
    grass = set()
    # Засеять траву случайными кластерами
    for _ in range(5):
        cx, cy = random.randint(0, WIDTH-1), random.randint(0, HEIGHT-1)
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and random.random() < 0.6:
                    grass.add((nx, ny))

    prey_list = []
    for _ in range(PREY_INITIAL):
        x, y = random.randint(0, WIDTH-1), random.randint(0, HEIGHT-1)
        prey_list.append(Entity(x, y, PREY_ENERGY_START))

    predator_list = []
    for _ in range(PREDATOR_INITIAL):
        x, y = random.randint(0, WIDTH-1), random.randint(0, HEIGHT-1)
        predator_list.append(Entity(x, y, PREDATOR_ENERGY_START))

    return grass, prey_list, predator_list


def find_nearest(entity, targets):
    """Найти ближайшую цель и сделать шаг к ней."""
    if not targets:
        return None
    best = None
    best_dist = float('inf')
    for t in targets:
        if isinstance(t, tuple):
            tx, ty = t
        else:
            tx, ty = t.x, t.y
        dist = abs(entity.x - tx) + abs(entity.y - ty)
        if dist < best_dist:
            best_dist = dist
            best = (tx, ty)
    return best


def move_toward(entity, target):
    """Сделать один шаг к цели."""
    if target is None:
        # Случайное движение
        entity.x = max(0, min(WIDTH-1, entity.x + random.randint(-1, 1)))
        entity.y = max(0, min(HEIGHT-1, entity.y + random.randint(-1, 1)))
        return
    tx, ty = target
    dx = 0 if tx == entity.x else (1 if tx > entity.x else -1)
    dy = 0 if ty == entity.y else (1 if ty > entity.y else -1)
    entity.x = max(0, min(WIDTH-1, entity.x + dx))
    entity.y = max(0, min(HEIGHT-1, entity.y + dy))


def step(grass, prey_list, predator_list):
    """Один шаг симуляции."""
    # 1. Рост травы
    new_grass = set(grass)
    # Рост рядом с существующей
    for gx, gy in grass:
        for nx, ny in neighbors(gx, gy):
            if (nx, ny) not in new_grass and random.random() < GRASS_GROW_PROB:
                new_grass.add((nx, ny))
    # Спонтанное появление (дождь / семена ветром)
    for _ in range(3):
        sx, sy = random.randint(0, WIDTH-1), random.randint(0, HEIGHT-1)
        if (sx, sy) not in new_grass:
            new_grass.add((sx, sy))
    grass = new_grass

    # 2. Движение и питание травоядных
    new_prey = []
    prey_positions = {}  # для быстрого поиска хищниками

    for p in prey_list:
        p.energy -= 1
        if p.energy <= 0:
            continue

        # Найти ближайшую траву в радиусе видимости
        visible_grass = [(gx, gy) for gx, gy in grass
                         if abs(gx - p.x) <= 5 and abs(gy - p.y) <= 5]
        target = find_nearest(p, visible_grass)
        move_toward(p, target)

        # Съесть траву, если на ней стоим
        if (p.x, p.y) in grass:
            grass.discard((p.x, p.y))
            p.energy += PREY_ENERGY_FROM_GRASS

        # Размножение
        if p.energy >= PREY_REPRODUCE_THRESHOLD:
            p.energy -= PREY_REPRODUCE_COST
            child = Entity(p.x, p.y, PREY_REPRODUCE_COST)
            new_prey.append(child)

        new_prey.append(p)
        prey_positions[(p.x, p.y)] = p

    prey_list = new_prey

    # 3. Движение и питание хищников
    new_predators = []
    for pred in predator_list:
        pred.energy -= PREDATOR_ENERGY_COST_PER_STEP
        if pred.energy <= 0:
            continue

        # Найти ближайшую добычу в радиусе видимости
        visible_prey = [p for p in prey_list
                        if p.alive and abs(p.x - pred.x) <= 4 and abs(p.y - pred.y) <= 4]
        target_entity = None
        if visible_prey:
            closest = find_nearest(pred, visible_prey)
            move_toward(pred, closest)
        else:
            move_toward(pred, None)

        # Съесть добычу — рядом, но с вероятностью (добыча может убежать)
        eaten = False
        for p in prey_list:
            if p.alive and abs(p.x - pred.x) <= 1 and abs(p.y - pred.y) <= 1 and random.random() < 0.3:
                p.alive = False
                pred.energy += PREDATOR_ENERGY_FROM_PREY
                eaten = True
                break

        # Размножение
        if pred.energy >= PREDATOR_REPRODUCE_THRESHOLD:
            pred.energy -= PREDATOR_REPRODUCE_COST
            child = Entity(pred.x, pred.y, PREDATOR_REPRODUCE_COST)
            new_predators.append(child)

        new_predators.append(pred)

    predator_list = new_predators
    prey_list = [p for p in prey_list if p.alive]

    return grass, prey_list, predator_list


def render(grass, prey_list, predator_list, step_num):
    """Вывести состояние мира."""
    grid = [[EMPTY]*WIDTH for _ in range(HEIGHT)]

    for gx, gy in grass:
        grid[gy][gx] = GRASS

    for p in prey_list:
        if 0 <= p.y < HEIGHT and 0 <= p.x < WIDTH:
            grid[p.y][p.x] = PREY

    for pred in predator_list:
        if 0 <= pred.y < HEIGHT and 0 <= pred.x < WIDTH:
            grid[pred.y][pred.x] = PREDATOR

    border = '+' + '-'*WIDTH + '+'
    print(f"\n--- Шаг {step_num} ---")
    print(border)
    for row in grid:
        print('|' + ''.join(row) + '|')
    print(border)
    print(f"  Трава: {len(grass)}  Травоядные: {len(prey_list)}  Хищники: {len(predator_list)}")


def main():
    random.seed(42)
    grass, prey_list, predator_list = init_world()

    history = []

    for s in range(STEPS):
        grass, prey_list, predator_list = step(grass, prey_list, predator_list)
        history.append((len(grass), len(prey_list), len(predator_list)))

        if s % PRINT_EVERY == 0 or s == STEPS - 1:
            render(grass, prey_list, predator_list, s)

        # Если всё вымерло — остановиться
        if len(prey_list) == 0 and len(predator_list) == 0:
            print(f"\n[Всё вымерло на шаге {s}]")
            break

    # Итоговая статистика
    print("\n=== Динамика популяций ===")
    print(f"{'Шаг':>5} {'Трава':>8} {'Травоядные':>12} {'Хищники':>10}")
    for i, (g, p, pr) in enumerate(history):
        if i % 20 == 0 or i == len(history) - 1:
            print(f"{i:>5} {g:>8} {p:>12} {pr:>10}")

    # Простая ASCII-гистограмма популяций
    print("\n=== Популяция травоядных (ASCII) ===")
    max_prey = max(h[1] for h in history) if history else 1
    for i in range(0, len(history), 5):
        bar_len = int(history[i][1] / max(max_prey, 1) * 50)
        print(f"{i:>4} |{'█' * bar_len}")

    print("\n=== Популяция хищников (ASCII) ===")
    max_pred = max(h[2] for h in history) if history else 1
    for i in range(0, len(history), 5):
        bar_len = int(history[i][2] / max(max_pred, 1) * 50)
        print(f"{i:>4} |{'█' * bar_len}")


if __name__ == '__main__':
    main()
