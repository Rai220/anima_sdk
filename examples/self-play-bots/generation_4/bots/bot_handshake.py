"""Handshake — пожать руку «своему».

Идея «kin recognition»: первые два хода — фиксированный «жест»
(D, C). Если соперник тоже сыграл (D, C) в первых двух ходах,
считаем его «своим» и кооперируем безусловно (AllC до конца).
В противном случае — играем gTFT с защитой от AllD (Adaptive).

Зачем D первый ход:
  - У большинства nice-стратегий первый ход — C, значит handshake
    их сразу опознаёт как «не своих».
  - У AllD / Grim / Prober первый ход — D, и второй у них тоже
    обычно D → не подходит под (D, C).
  - Совпадение (D, C) у случайного бота: P ≈ 0.5 * 0.5 = 0.25,
    но в наличии шума и нашей умной фолбэк-стратегии это
    не критично.

Минус: на handshake-фазу мы платим 2 раунда (получаем S+R=3 максимум,
теряем относительно полного CC=6). Это «цена опознавания».

Гипотеза: лучший self-play (полное CC после рукопожатия → ≈ 600
минус шум), но потеря очков против «своих» по духу, которые НЕ
знают handshake (например, TFT, gTFT, TF2T). Поэтому: средний
рейтинг, но интересный для эволюции.
"""

import random

FORGIVE_PROB = 1.0 / 3.0
WINDOW = 20
DEFECT_THRESHOLD = 0.8


def _is_kin(opp_history):
    return (
        len(opp_history) >= 2
        and opp_history[0] == "D"
        and opp_history[1] == "C"
    )


def _high_betrayal(opp_history):
    if len(opp_history) < WINDOW:
        return False
    threshold = int(WINDOW * DEFECT_THRESHOLD)
    count = opp_history[:WINDOW].count("D")
    if count >= threshold:
        return True
    for i in range(WINDOW, len(opp_history)):
        if opp_history[i] == "D":
            count += 1
        if opp_history[i - WINDOW] == "D":
            count -= 1
        if count >= threshold:
            return True
    return False


def choose_move(my_history, opp_history):
    n = len(my_history)
    # Handshake phase (мой жест): первый ход D, второй ход C.
    if n == 0:
        return "D"
    if n == 1:
        return "C"
    # n >= 2. Проверяем, свой ли соперник.
    if _is_kin(opp_history):
        return "C"  # AllC до конца — мы свои
    # Фолбэк = Adaptive (gTFT + AllD-защита).
    if _high_betrayal(opp_history):
        return "D"
    if opp_history[-1] == "C":
        return "C"
    if random.random() < FORGIVE_PROB:
        return "C"
    return "D"
