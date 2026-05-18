"""Random — flips a fair coin every round."""
import random


def choose_move(my_history, opp_history):
    return "C" if random.random() < 0.5 else "D"
