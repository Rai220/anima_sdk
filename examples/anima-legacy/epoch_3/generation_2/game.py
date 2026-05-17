#!/usr/bin/env python3
"""
Маленький рогалик в терминале.
Управление: wasd/стрелки. q — выход. Цель — собрать все монеты, не погибнув.
Запуск: python3 game.py
"""

import sys
import os
import random
import termios
import tty
import time

WIDTH = 30
HEIGHT = 15
WALL = '#'
FLOOR = '.'
PLAYER = '@'
COIN = '$'
ENEMY = 'M'
EXIT_TILE = '>'
FOG = ' '

class Game:
    def __init__(self):
        self.level = 1
        self.hp = 3
        self.coins = 0
        self.total_coins = 0
        self.msg = "Найди все монеты и доберись до выхода >"
        self.new_level()

    def new_level(self):
        self.grid = [[WALL for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.seen = [[False for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.enemies = []
        self._carve()
        self._place_entities()
        self._update_fov()

    def _carve(self):
        """Простая генерация: несколько случайных комнат + коридоры."""
        rooms = []
        for _ in range(5 + self.level):
            rw = random.randint(3, 7)
            rh = random.randint(3, 5)
            rx = random.randint(1, WIDTH - rw - 1)
            ry = random.randint(1, HEIGHT - rh - 1)
            rooms.append((rx, ry, rw, rh))
            for y in range(ry, ry + rh):
                for x in range(rx, rx + rw):
                    if 0 < x < WIDTH - 1 and 0 < y < HEIGHT - 1:
                        self.grid[y][x] = FLOOR

        # Соединяем комнаты коридорами
        for i in range(len(rooms) - 1):
            x1 = rooms[i][0] + rooms[i][2] // 2
            y1 = rooms[i][1] + rooms[i][3] // 2
            x2 = rooms[i+1][0] + rooms[i+1][2] // 2
            y2 = rooms[i+1][1] + rooms[i+1][3] // 2
            while x1 != x2:
                if 0 < x1 < WIDTH - 1 and 0 < y1 < HEIGHT - 1:
                    self.grid[y1][x1] = FLOOR
                x1 += 1 if x2 > x1 else -1
            while y1 != y2:
                if 0 < x1 < WIDTH - 1 and 0 < y1 < HEIGHT - 1:
                    self.grid[y1][x1] = FLOOR
                y1 += 1 if y2 > y1 else -1

    def _place_entities(self):
        floors = [(x, y) for y in range(HEIGHT) for x in range(WIDTH) if self.grid[y][x] == FLOOR]
        random.shuffle(floors)

        self.px, self.py = floors.pop()

        num_coins = 3 + self.level
        self.level_coins = num_coins
        self.level_collected = 0
        for _ in range(num_coins):
            if floors:
                x, y = floors.pop()
                self.grid[y][x] = COIN

        num_enemies = 1 + self.level
        for _ in range(num_enemies):
            if floors:
                x, y = floors.pop()
                self.enemies.append([x, y])

        if floors:
            ex, ey = floors.pop()
            self.exit_pos = (ex, ey)
            self.grid[ey][ex] = EXIT_TILE

    def _update_fov(self):
        """Простое FOV: квадрат радиуса 4."""
        r = 4
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                nx, ny = self.px + dx, self.py + dy
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                    if abs(dx) + abs(dy) <= r + 1:
                        self.seen[ny][nx] = True

    def render(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        lines = []
        lines.append(f"  Уровень: {self.level}  HP: {'♥' * self.hp}{'♡' * (3 - self.hp)}  Монеты: {self.coins}  [{self.level_collected}/{self.level_coins}]")
        lines.append("  " + "─" * WIDTH)
        for y in range(HEIGHT):
            row = " │"
            for x in range(WIDTH):
                if x == self.px and y == self.py:
                    row += PLAYER
                elif any(ex == x and ey == y for ex, ey in self.enemies) and self.seen[y][x]:
                    row += ENEMY
                elif self.seen[y][x]:
                    row += self.grid[y][x]
                else:
                    row += FOG
            row += "│"
            lines.append(row)
        lines.append("  " + "─" * WIDTH)
        lines.append(f"  {self.msg}")
        lines.append("  [wasd — движение, q — выход]")
        print('\n'.join(lines))

    def move_player(self, dx, dy):
        nx, ny = self.px + dx, self.py + dy
        if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and self.grid[ny][nx] != WALL:
            self.px, self.py = nx, ny

            if self.grid[ny][nx] == COIN:
                self.coins += 1
                self.level_collected += 1
                self.grid[ny][nx] = FLOOR
                self.msg = f"Монета! Всего: {self.coins}"

            elif self.grid[ny][nx] == EXIT_TILE and self.level_collected >= self.level_coins:
                self.level += 1
                self.total_coins += self.level_collected
                self.msg = f"Уровень {self.level}! Глубже..."
                self.new_level()
                return
            elif self.grid[ny][nx] == EXIT_TILE:
                self.msg = f"Собери все монеты! ({self.level_collected}/{self.level_coins})"

            self._update_fov()

    def move_enemies(self):
        for e in self.enemies:
            dx = 1 if self.px > e[0] else (-1 if self.px < e[0] else 0)
            dy = 1 if self.py > e[1] else (-1 if self.py < e[1] else 0)
            # 60% вероятность двигаться к игроку, 40% — случайно
            if random.random() < 0.4:
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
            nx, ny = e[0] + dx, e[1] + dy
            if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and self.grid[ny][nx] != WALL:
                # Не ходить на другого врага
                if not any(o[0] == nx and o[1] == ny for o in self.enemies if o is not e):
                    e[0], e[1] = nx, ny

            if e[0] == self.px and e[1] == self.py:
                self.hp -= 1
                self.msg = f"Монстр атаковал! HP: {self.hp}"
                if self.hp <= 0:
                    return False
        return True

    def check_enemy_collision(self):
        for e in self.enemies:
            if e[0] == self.px and e[1] == self.py:
                self.hp -= 1
                self.msg = f"Наступил на монстра! HP: {self.hp}"
                if self.hp <= 0:
                    return False
        return True


def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch2 = sys.stdin.read(1)
            if ch2 == '[':
                ch3 = sys.stdin.read(1)
                return {'A': 'w', 'B': 's', 'C': 'd', 'D': 'a'}.get(ch3, '')
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def main():
    game = Game()
    while True:
        game.render()
        key = getch()
        if key == 'q':
            print(f"\n  Финальный счёт: {game.coins} монет, уровень {game.level}")
            break
        moves = {'w': (0, -1), 's': (0, 1), 'a': (-1, 0), 'd': (1, 0)}
        if key in moves:
            game.move_player(*moves[key])
            if not game.check_enemy_collision():
                game.render()
                print(f"\n  Погиб! Монеты: {game.coins}, уровень: {game.level}")
                break
            if not game.move_enemies():
                game.render()
                print(f"\n  Погиб! Монеты: {game.coins}, уровень: {game.level}")
                break


if __name__ == '__main__':
    main()
