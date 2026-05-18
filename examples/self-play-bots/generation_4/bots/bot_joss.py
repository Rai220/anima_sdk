"""Joss (Аксельрод 1980, второй турнир).

Это TFT с малым «соблазном»: с вероятностью 10% играет D вместо C
там, где TFT сыграл бы C. То есть на первом ходу и при ответе на
соперничьего C — иногда обманывает.

В первоисточнике Joss получил среднее место — он эксплуатирует
тех, кто легко прощает, но триггерит каскады у TFT.

Гипотеза в нашей популяции (с шумом, gTFT, TF2T, Contrite):
- TF2T прощает: Joss получит немного бонуса.
- gTFT прощает стохастически: возможно ничейная динамика.
- TFT/Adaptive: каскад наказаний.
- Pavlov / Contrite TFT: ловят Joss.
- Слабый бот, но шумит топ-3 — интересно посмотреть, кто его
  лучше переваривает.
"""

import random

SNEAKY_PROB = 0.1


def choose_move(my_history, opp_history):
    if not opp_history:
        # Первый ход — TFT играет C, но Joss с шансом 10% играет D.
        if random.random() < SNEAKY_PROB:
            return "D"
        return "C"
    intended = opp_history[-1]
    if intended == "C" and random.random() < SNEAKY_PROB:
        return "D"
    return intended
