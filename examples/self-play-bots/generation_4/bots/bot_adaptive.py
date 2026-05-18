"""Adaptive — обнаруживает «всегда-предателей» и переключается в D.

Логика двух режимов:
  1) Cooperative mode (по умолчанию): играет как gTFT — первый ход C,
     дальше копирует соперника, прощая одиночное D с вероятностью
     1/3.
  2) Defection mode: если в истории есть момент, когда в окне
     последних 20 ходов соперник сыграл D ≥ 80% — закрепляемся в
     постоянном D до конца матча, без возврата.

Почему окно 20 ходов и порог 80%:
  - При noise=0.02 у nice-бота ожидаемая доля D = ~2% (только шум).
    Чтобы получить 80% D в окне 20 ходов, нужно ≥16 D, вероятность
    ничтожна.
  - Для AllD ожидаемая доля D = ~98% → быстро срабатывает.
  - Окно достаточно короткое, чтобы реагировать оперативно.

Важная деталь реализации: НЕ держим состояние между раундами в
модуле, чтобы было безопасно играть self-play (когда обе стороны —
один и тот же модуль). Решение пересчитываем из истории.

Свойства:
  - Против AllC, TFT, TF2T, gTFT, Soft Maj: остаётся в gTFT-режиме,
    т.е. примерно идентичен gTFT.
  - Против AllD: быстро (через 20 ходов) переключается в D и
    закрепляется в DD. Ловит ~1·(N-20) = 180 P-очков плюс штраф
    первых 20.
  - Против Grim: после шумового D Grim'а оба уходят в DD; окно
    Adaptive видит 80%+ D соперника, фиксируется в D.
  - Против Random (50% D): не дотягивает до 80%, остаётся в
    gTFT-режиме.

Гипотеза: должен побить gTFT за счёт того, что vs AllD/Grim
играет «правильно» (DD) вместо «вечно прощать». Стоит проверить.
"""

import random

FORGIVE_PROB = 1.0 / 3.0
WINDOW = 20
DEFECT_THRESHOLD = 0.8  # >=16 D из 20


def _has_been_betrayed(opp_history):
    """True, если в какой-то момент окно последних 20 ходов соперника
    содержало >= 80% D. Раз обнаружив — не возвращаемся."""
    if len(opp_history) < WINDOW:
        return False
    threshold_count = int(WINDOW * DEFECT_THRESHOLD)  # 16
    # Скользящее окно: считаем D в каждом окне длины WINDOW.
    count = opp_history[:WINDOW].count("D")
    if count >= threshold_count:
        return True
    for i in range(WINDOW, len(opp_history)):
        # окно [i-WINDOW+1, i] получаем из [i-WINDOW, i-1] добавив
        # opp_history[i] и убрав opp_history[i-WINDOW].
        if opp_history[i] == "D":
            count += 1
        if opp_history[i - WINDOW] == "D":
            count -= 1
        if count >= threshold_count:
            return True
    return False


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    if _has_been_betrayed(opp_history):
        return "D"
    if opp_history[-1] == "C":
        return "C"
    if random.random() < FORGIVE_PROB:
        return "C"
    return "D"
