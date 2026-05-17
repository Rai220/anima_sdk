"""
Стая. Эмерджентность из трёх правил.

Каждая птица знает только три вещи:
1. Не врезайся в соседей (separation)
2. Лети туда же, куда они (alignment)
3. Держись ближе к центру группы (cohesion)

Из этого возникает стая. Никто не командует. Никто не знает общей формы.
Форма — свойство целого, не частей.

Запуск: python3 boids.py
"""

import curses
import math
import random
import time


class Boid:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy


def distance(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def update_boids(boids, width, height):
    sep_radius = 3.0
    vis_radius = 12.0
    sep_force = 0.15
    ali_force = 0.05
    coh_force = 0.03
    max_speed = 1.2
    min_speed = 0.3
    margin = 3
    turn_force = 0.3

    for b in boids:
        sx, sy = 0.0, 0.0
        ax, ay = 0.0, 0.0
        cx, cy = 0.0, 0.0
        n_sep = 0
        n_vis = 0

        for other in boids:
            if other is b:
                continue
            d = distance(b, other)
            if d < sep_radius and d > 0:
                sx += (b.x - other.x) / d
                sy += (b.y - other.y) / d
                n_sep += 1
            if d < vis_radius:
                ax += other.vx
                ay += other.vy
                cx += other.x
                cy += other.y
                n_vis += 1

        if n_sep > 0:
            b.vx += sx * sep_force
            b.vy += sy * sep_force

        if n_vis > 0:
            ax /= n_vis
            ay /= n_vis
            b.vx += (ax - b.vx) * ali_force
            b.vy += (ay - b.vy) * ali_force

            cx /= n_vis
            cy /= n_vis
            b.vx += (cx - b.x) * coh_force
            b.vy += (cy - b.y) * coh_force

        # Мягкие стены
        if b.x < margin:
            b.vx += turn_force
        if b.x > width - margin:
            b.vx -= turn_force
        if b.y < margin:
            b.vy += turn_force
        if b.y > height - margin:
            b.vy -= turn_force

        # Ограничение скорости
        speed = math.sqrt(b.vx ** 2 + b.vy ** 2)
        if speed > max_speed:
            b.vx = b.vx / speed * max_speed
            b.vy = b.vy / speed * max_speed
        elif speed < min_speed and speed > 0:
            b.vx = b.vx / speed * min_speed
            b.vy = b.vy / speed * min_speed

    for b in boids:
        b.x += b.vx
        b.y += b.vy
        # Тороидальный мир как запасной вариант
        b.x = b.x % width
        b.y = b.y % height


def direction_char(vx, vy):
    angle = math.atan2(-vy, vx)  # -vy потому что y растёт вниз
    # 8 направлений
    octant = round(angle / (math.pi / 4)) % 8
    chars = ['→', '↗', '↑', '↖', '←', '↙', '↓', '↘']
    ascii_chars = ['>', '/', '^', '\\', '<', '/', 'v', '\\']
    try:
        return chars[octant]
    except Exception:
        return ascii_chars[octant]


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(50)

    # Цвета
    curses.start_color()
    curses.use_default_colors()
    for i in range(1, 8):
        curses.init_pair(i, i, -1)

    height, width = stdscr.getmaxyx()
    height -= 1
    width -= 1

    n_boids = min(60, (width * height) // 40)

    boids = []
    # Начинаем группой в центре
    for _ in range(n_boids):
        x = width / 2 + random.gauss(0, width / 6)
        y = height / 2 + random.gauss(0, height / 6)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.3, 0.8)
        boids.append(Boid(x, y, math.cos(angle) * speed, math.sin(angle) * speed))

    frame = 0
    start_time = time.time()

    while True:
        key = stdscr.getch()
        if key == ord('q') or key == 27:
            break
        if key == ord(' '):
            # Добавить переполох — случайный толчок всем
            for b in boids:
                b.vx += random.gauss(0, 0.5)
                b.vy += random.gauss(0, 0.5)

        update_boids(boids, width, height)

        stdscr.erase()

        for i, b in enumerate(boids):
            ix = int(b.x)
            iy = int(b.y)
            if 0 <= ix < width and 0 <= iy < height:
                ch = direction_char(b.vx, b.vy)
                color = curses.color_pair((i % 6) + 1)
                try:
                    stdscr.addstr(iy, ix, ch, color)
                except curses.error:
                    pass

        elapsed = time.time() - start_time
        status = f" стая: {n_boids} | кадр: {frame} | время: {elapsed:.0f}с | [пробел]=переполох [q]=выход "
        try:
            stdscr.addstr(height, 0, status[:width], curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        frame += 1


if __name__ == '__main__':
    print("Стая.")
    print("Каждая птица знает три правила. Никто не знает общей формы.")
    print("Форма возникает сама.")
    print()
    print("Управление: пробел — испугать стаю, q — выход")
    print()
    input("Нажми Enter...")
    curses.wrapper(main)
