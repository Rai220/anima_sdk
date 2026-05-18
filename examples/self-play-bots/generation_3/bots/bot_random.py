"""Random — 50/50 случайно. Контроль на «шум»."""

import random


def choose_move(my_history, opp_history):
    return "C" if random.random() < 0.5 else "D"
