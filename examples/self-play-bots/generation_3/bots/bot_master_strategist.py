"""Master Strategist — мета-стратегия с классификацией оппонента.

Идея: вместо одной фиксированной логики (TFT, gTFT, Hardener, ZD)
сначала классифицировать соперника по поведению за окно, потом
переключиться в подходящий режим. Это синтез уроков T1-T23:

  - vs кооператоры (AAC, Soft, Omega, gTFT, TFT и т.п.) — gTFT
    с прощением 1/3, как теоретически оптимальный mode.
  - vs упрямые D-стратегии (AllD, Grim после моего шумового D,
    Gradual в каскаде) — AllD без сожалений.
  - vs периодические провокаторы (Tester DCDC, RevPav DCC,
    Prober DDDD-then-C) — AllD после детекции цикла.
  - vs Pavlov-семейство (WSLS, реагирует на счёт) — TFT-like
    жёсткий, без forgiveness, иначе Pavlov эксплуатирует.
  - vs Random — TFT (mirror), нельзя ничего предсказать.

Принципы Аксельрода соблюдены:
  - nice: первый ход всегда C, default режим — gTFT (forgiving).
  - retaliatory: режим AllD при детекции эксплуатации.
  - forgiving: gTFT-режим прощает с p=1/3.
  - non-envious: не пытается «обогнать» — переключение защищает,
    не предаёт первым.

Архитектура:
  - Фаза 1 (n < 6): чистый TFT, чтобы дать сопернику показать себя.
  - Фаза 2 (n = 6..29): продолжаем TFT, копим статистику.
  - Фаза 3 (n >= 30): классифицируем и переключаемся.
  - После переключения: «sticky» — режим не меняется (защита от
    манипуляторов, которые сначала прикидываются плохими, потом
    хорошими).

Детекторы (применяются на n=30, потом mode фиксируется):
  - period detector (как в PD): для p=2,3,4 проверить, что
    opp_history[-12:] = (cycle * (12/p)) с цикл, содержащим и C, и D.
  - opp_C_ratio в окне n=10..29 (последние 20 ходов).
  - reactive: после моих D-ходов в окне, доля D-ответов опп
    в следующем ходе.

Стохастичность: gTFT-режим использует свой rng.
"""

import random

_rng = random.Random()

WARMUP_TFT = 6           # первые 6 ходов чистый TFT
CLASSIFY_AT = 30         # на этом ходе фиксируем mode
WINDOW = 20              # окно последних ходов для статистики
GENEROSITY = 1.0 / 3.0   # для gTFT-режима

# Возможные режимы
MODE_GTFT = "gtft"
MODE_TFT = "tft"
MODE_ALLD = "alld"


def _detect_period(opp_history):
    """Вернуть период (2,3,4) если последние 12 ходов опп = cycle*3
    с cycle, содержащим И C, И D. Иначе None."""
    if len(opp_history) < 12:
        return None
    tail = opp_history[-12:]
    for p in (2, 3, 4):
        candidate = tail[:p]
        if "C" not in candidate or "D" not in candidate:
            continue
        ok = all(tail[i] == candidate[i % p] for i in range(12))
        if ok:
            return p
    return None


def _classify(my_history, opp_history):
    """Вернуть один из MODE_*. Вызывается один раз на ходу 30."""
    # 1. Periodic provocateur — AllD.
    if _detect_period(opp_history) is not None:
        return MODE_ALLD

    # 2. Доля кооперации опп за последнее окно.
    window = opp_history[-WINDOW:]
    c_ratio = window.count("C") / len(window)

    # 3. Reactive: после моего D — сколько D ответов опп?
    my_window = my_history[-WINDOW:]
    d_indices = [i for i, m in enumerate(my_window[:-1]) if m == "D"]
    if d_indices:
        retaliations = sum(
            1 for i in d_indices if opp_history[-WINDOW + i + 1] == "D"
        )
        reactive_ratio = retaliations / len(d_indices)
    else:
        reactive_ratio = 0.5  # нет данных — нейтрально

    # 4. Решающее правило.
    # Очень мало C → AllD (бессмысленно прощать).
    if c_ratio < 0.30:
        return MODE_ALLD
    # Высокая кооперация + слабая реакция → mostly-AllC-like → gTFT
    # (не эксплуатируем, удерживаем CC).
    if c_ratio >= 0.85:
        return MODE_GTFT
    # Средний C + сильная реакция → классический TFT/Pavlov-семейство.
    # Для устойчивости берём gTFT (прощает шум).
    if reactive_ratio >= 0.6:
        return MODE_GTFT
    # Средний C + слабая реакция → манипулятор? Берём TFT (mirror).
    return MODE_TFT


# Состояние «sticky» — мы храним mode в замыкании по id ботов нельзя,
# потому что бот - это просто функция. Сохраняем через атрибут функции.
def _get_state():
    if not hasattr(choose_move, "_state"):
        choose_move._state = {"mode": None, "match_id": None}
    return choose_move._state


def choose_move(my_history, opp_history):
    # Восстановим состояние, но сбрасываем при новом матче.
    # Признак нового матча: my_history пуст.
    state = _get_state()
    n = len(my_history)
    if n == 0:
        state["mode"] = None
        return "C"  # nice

    # Фаза warmup: чистый TFT.
    if n < WARMUP_TFT:
        return "D" if opp_history[-1] == "D" else "C"

    # Фаза накопления: продолжаем TFT.
    if n < CLASSIFY_AT:
        return "D" if opp_history[-1] == "D" else "C"

    # На ходу CLASSIFY_AT — классифицируем один раз.
    if state["mode"] is None:
        state["mode"] = _classify(my_history, opp_history)

    mode = state["mode"]
    if mode == MODE_ALLD:
        return "D"
    if mode == MODE_TFT:
        return "D" if opp_history[-1] == "D" else "C"
    # MODE_GTFT
    if opp_history[-1] == "C":
        return "C"
    if _rng.random() < GENEROSITY:
        return "C"
    return "D"
