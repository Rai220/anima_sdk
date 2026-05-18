"""Tit-for-Tat (TFT).

Победитель оригинальных турниров Аксельрода. Простое правило:
первый ход — C, дальше копия последнего хода соперника. Nice +
retaliatory + forgiving (одно D соперника → одно D в ответ, потом
снова C), но плохо переносит шум: одиночная "шумовая" D вызывает
бесконечный взаимный обмен D-C.
"""


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    return opp_history[-1]
