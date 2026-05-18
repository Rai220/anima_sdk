"""Random — 50/50 случайное C или D.

Без истории, без памяти, без стратегии. Базовый бенчмарк для проверки,
что более сложные стратегии хоть чем-то лучше шума.
"""

import random


def choose_move(my_history, opp_history):
    return "C" if random.random() < 0.5 else "D"
