"""ZD-GTFT-2 — Zero-Determinant Generous (Stewart & Plotkin, 2013).

Memory-1 стохастическая стратегия из класса Zero-Determinant
(Press & Dyson, PNAS 2012). В отличие от ZD-Extortion, ZD-GTFT-2
**provably-cooperative** — она навязывает линейное соотношение
выплат, при котором соперник максимизирует свой счёт только
полной кооперацией (играя AllC соперник получает максимум 3,
играя AllD — получает P=1).

Формально: для нашей матрицы (T=5, R=3, P=1, S=0) параметр
extortion-фактора chi=2 (Stewart-Plotkin "GTFT-2") даёт вероятности
кооперации, условные на исходе предыдущего раунда:

    p_CC = 1     # после взаимной кооперации — всегда C
    p_CD = 1/8   # я сыграл C, опп предал → почти всегда наказываю
    p_DC = 1     # я сыграл D, опп простил → всегда возвращаюсь к C
    p_DD = 1/4   # после взаимного D — иногда прощаю первым

Первый ход — C (бот «nice»).

Свойства:
- self-play: цикл сходится к (C,C) даже под шумом, потому что
  p_DD=1/4 со временем выводит из DD; ожидаю ~580 за матч.
- vs AllC: всегда (C,C) → 600 (минус шум).
- vs AllD: попадает в DD-режим, p_DD=1/4 даёт ~25% C → ~150 очков.
  Хуже чем TFT (~210), потому что ZD «прощает» AllD.
- vs TFT/gTFT/Omega: должно стабильно держать высокую кооперацию.
- vs Pavlov/RevPav: ZD навязывает линейное соотношение — должно
  работать как «магнит» к кооперации.

Стохастичность: свой rng, не зависящий от внешнего seed.

Сравнение с gTFT:
- gTFT прощает только в одном случае: opp D, я отвечаю C с p=1/3.
- ZD-GTFT-2 имеет четыре разных вероятности, и они вычислены так,
  чтобы навязать соотношение S_opp = chi * S_me + (1-chi) * P
  в пределе длинного матча. Это математически другая концепция
  (не эвристика, а провабельная гарантия).
"""

import random

_rng = random.Random()

# Stewart-Plotkin ZDGTFT-2 для T=5, R=3, P=1, S=0, chi=2.
P_CC = 1.0
P_CD = 1.0 / 8.0
P_DC = 1.0
P_DD = 1.0 / 4.0


def choose_move(my_history, opp_history):
    # Первый ход — кооперация.
    if not my_history:
        return "C"
    my_last = my_history[-1]
    opp_last = opp_history[-1]
    if my_last == "C" and opp_last == "C":
        p = P_CC
    elif my_last == "C" and opp_last == "D":
        p = P_CD
    elif my_last == "D" and opp_last == "C":
        p = P_DC
    else:  # DD
        p = P_DD
    return "C" if _rng.random() < p else "D"
