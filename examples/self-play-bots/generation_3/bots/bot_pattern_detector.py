"""Pattern Detector — TFT + общий детектор периодических эксплоитов.

Мотивация (T21 анализ):
  Adaptive Hardener закрыл AllD-семейство (vs AllD: -10 вместо -347),
  но Tester (DCDC после "голубя"), Reverse Pavlov (циклы периода 2-3
  vs TFT) и Joss (TFT с редкими D) по-прежнему доят gTFT/TFT-семью.
  Эти боты сидят на доле T=5 за каждый второй раунд цикла.

  Anti-Alternator решает только RevPav (специальный детектор).
  Adaptive Defender решает только Prober (специальная сигнатура).
  Нет ОБЩЕГО механизма "опп играет периодически — играю best response".

Гипотеза Pattern Detector:
  Если соперник играет с периодом p in {2, 3, 4} и в цикле есть
  и C, и D — best response = AllD (доказывается ниже). Достаточно
  детектировать цикл и переключиться.

Best response к чистому периоду p (mix C/D):
  Допустим в цикле длины p у опп есть k штук C и (p-k) штук D.
  Если я играю AllD → за цикл я набираю k*T + (p-k)*P = 5k + (p-k) =
    4k + p очков; в среднем (4k + p) / p за раунд.
  Если я играю AllC → 3k + 0*(p-k) = 3k очков; в среднем 3k/p.
  Если я играю «зеркало» (повторяю их паттерн) → CC=R на C-позициях,
    DD=P на D-позициях: 3k + (p-k) = 2k + p очков; в среднем (2k + p) / p.
  AllD vs AllC: 4k + p > 3k ⇔ k > -p (всегда верно при p>0). ✓
  AllD vs зеркало: 4k + p > 2k + p ⇔ 2k > 0 (верно при k>=1). ✓

  Для p=2, k=1 (DCDC): AllD даёт (5+1)/2 = 3, зеркало даёт (3+1)/2 = 2,
  AllC даёт (0+3)/2 = 1.5. AllD строго лучший.

  Для p=3, k=1 (DDCDDC...): AllD даёт (1+1+5)/3 ≈ 2.33; зеркало даёт
  (1+1+3)/3 ≈ 1.67. AllD лучший.

Алгоритм:

  n = len(my_history).

  Warmup (n < 16): чистый TFT.
    - n=0: C.
    - n>=1: opp_history[-1] (копируем последний ход опп).
    - 16 ходов = 4 цикла периода 4 = 8 циклов периода 2. Достаточно
      для надёжной детекции.

  Detection (n >= 16): ищем период p in {2, 3, 4}, такой что
    opp_history[-2p:-p] совпадает с opp_history[-p:] (с допуском 1 шум).
    И цикл содержит И C, И D (исключаем pure C / pure D — для них есть
    другие стратегии).
    Берём наименьший p, который проходит.

  Если периодический паттерн с C/D найден → AllD (до конца матча
    оставаться в exploit_mode).

  Если не найден → продолжать TFT.

  Sticky mode: после первого срабатывания флаг exploit_mode = True
  до конца матча. Это потому, что:
  1. Опп может видеть наши D и сменить стратегию (например, Tester
     перейдёт в TFT после нашего ответного D на его первый D).
  2. После моих D opp_history больше не отражает чистый паттерн.
  3. Sticky защищает от ложных «выходов» из режима.

  Sticky выводится из истории stateless: проверяем, играл ли я D
  хотя бы 8 раз подряд в последних 12 ходах (с допуском шума). Если
  да — я в режиме AllD и продолжаю.

Ожидаемые матчи:

  vs Tester: opp = D, C, C, [TFT-mode] = mostly C (если я не ответил
    D на первый D). Однако я в warmup TFT → opp_history[1]=D triggers
    моё D на ход 2, что переключает Tester в TFT-режим, opp играет
    CCCCCCC... (после раунда ~5). pure C цикл → не триггерится
    pattern detector. Я в TFT vs Tester-TFT-mode → высокая CC.
    Pattern Detector НЕ улучшает vs Tester сравнимо с TFT.
    Hmm. Но если я после warmup детектирую DCDC в раундах 0-15
    (Tester чередует D/C на голубях, но я играю TFT, не голубь), то
    Tester видит мои D и переключается в TFT. DCDC цикл не закрепится.

  vs Reverse Pavlov: RevPav vs TFT даёт цикл (CC, CD, DC, CC, CD, DC, ...)
    периода 3 у меня (CDC, CDC, ...) и периода 3 у опп (CCD, CCD, ...).
    Wait, давай посмотрим точнее.
    RevPav: предыдущий (mh, oh) = (C, C) → win → shift → D.
    Я TFT: предыдущий oh = C → C.
    Начало: оба C, оба C. Раунд 1: opp играет D (win-shift), я C.
    Раунд 2: opp получил win (DC = win для opp T=5), shift → C. Я D (TFT).
    Раунд 3: opp проиграл (CD = S=0), stay → C. Я C (TFT).
    Раунд 4: opp выиграл (CC=R)... opp_pavlov: после R = win, shift → D.
    Цикл 3: opp = (D, C, C, D, C, C, ...). Это период 3 с k=1 (одна D).
    Detected! → exploit_mode → AllD.
    После переключения: opp видит мой D, считает (D, D) = win, shift → C.
    Я D. opp видит (D, C) = lose (S=0 для opp), stay → C. Я D.
    opp видит (D, C) = lose, stay → C. Я D, etc.
    Стабильно DC: я T=5, opp S=0. Тренд: я ≈ 200+5*180=200+900=1000.
    Но это нереалистично, потому что opp может перестать держать C.
    На самом деле RevPav опасается из (D,C) = lose → stay → C.
    Так что DC-лок стабилен. Я получаю ~5/раунд после переключения.

  vs Joss (TFT с редкими D): Joss играет D с малой вероятностью
    (~10%). В opp_history будет шумовая D-серия, без чистого периода.
    Detector не сработает. Я в TFT vs Joss → плохо (Joss дёр).
    Pattern Detector не улучшает vs Joss.

  vs AllC: opp_history = C, C, C, C (pure). Cycle has только C, не
    триггерится (mixed required). TFT vs AllC → CC всю игру.
    ≈ 575 (с шумом).

  vs AllD: opp_history = D, D, D, D (pure). Cycle has только D, не
    триггерится. TFT vs AllD → DD всю игру. ≈ 190.

  vs TFT: оба играют C-C (с шумовыми сбоями DD-каскад). Не триггерится
    (pure C основной режим). TFT vs TFT ≈ 520.

  vs Random: opp_history случайный. Случайные совпадения возможны,
    но низкая вероятность стабильного match для p=2,3,4 при noise=0.02.
    Иногда триггерится по случаю → AllD. Это хорошо vs Random
    (AllD vs Random ≈ 350 vs 50, у меня 350).

Шумоустойчивость:

  Допуск 1 шумовой бит при сравнении opp_history[-2p:-p] vs
  opp_history[-p:]. Для p=4 это 1/4 = 25% шума, что больше чем
  noise=0.02 → True period 4 пройдёт; случайное совпадение в Random
  нужно ≥7/8 совпадений (Random p=0.5 → вероятность ≈ C(8,1)/256 ≈
  3.5% за окно). Триггер редкий, не катастрофа.

  Sticky mode: после переключения остаюсь в AllD до конца матча.
  Это сильное предположение: если опп не периодический, я мог
  ошибиться и проиграл бы кооперативу. Но за 200 раундов AllD
  даёт стабильный exploit на истинно периодическом противнике.
"""


def _is_periodic(opp_history, p):
    """Проверить, что последние 3p ходов опп — повторение цикла длины p.

    Требования (жёсткие, чтобы не сработать на шумовых каскадах):
    - Нужно минимум 3p историй (3 полных цикла).
    - 0 несовпадений между opp_history[-3p:] и (candidate * 3).
    - Цикл содержит и C, и D (исключаем pure C/D).
    """
    if len(opp_history) < 3 * p:
        return False
    candidate = opp_history[-p:]
    if "C" not in candidate or "D" not in candidate:
        return False
    expected = candidate * 3
    actual = opp_history[-3 * p :]
    # 0 несовпадений — строгое требование. Шумовой каскад (cascade
    # после случайного D-флипа) даёт грязный паттерн, такая проверка
    # его отсеивает.
    return all(a == e for a, e in zip(actual, expected))


def _already_in_exploit(my_history, opp_history):
    """Эвристика sticky: я уже играл D много раз подряд недавно.

    Возвращает True, если в моих последних 12 ходах ≥ 9 штук D
    (с допуском шума). Это означает, что я уже в exploit_mode.
    """
    if len(my_history) < 12:
        return False
    recent = my_history[-12:]
    return recent.count("D") >= 9


def choose_move(my_history, opp_history):
    n = len(my_history)
    # Первый ход — nice.
    if n == 0:
        return "C"

    # Уже в режиме эксплуатации? Продолжаем AllD.
    if _already_in_exploit(my_history, opp_history):
        return "D"

    # Warmup: первые 20 ходов — Tit-For-Two-Tats (прощающий).
    # TF2T выбран, чтобы не порождать echo-каскады с TFT-семьёй под
    # шумом. Echo-каскад под шумом ВЫГЛЯДИТ как период 2 DCDC, и
    # сломанный детектор начинает эксплуатировать своих кооператоров.
    # TF2T прощает одиночные D (включая шумовые), echo-каскад
    # затухает сам собой.
    if n < 20:
        if n < 2:
            return "C"
        # Карать только если последние 2 хода опп — оба D.
        if opp_history[-1] == "D" and opp_history[-2] == "D":
            return "D"
        return "C"

    # Detection: периодический паттерн с C/D?
    # Дополнительная защита: проверяем, что моя собственная история
    # не является зеркалом того же периода (echo cascade).
    for p in (2, 3, 4):
        if not _is_periodic(opp_history, p):
            continue
        # Проверка на echo-каскад: если my_history тоже периодична с
        # тем же p И моя цикла содержит D, значит мы оба болтаемся в
        # цикле (TFT echo под шумом). НЕ эксплуатируем — это
        # ложный сигнал от шумового каскада.
        # Если my_history полностью кооперативна (только C в цикле),
        # это не echo — это правильный сигнал, что опп сидит в цикле,
        # а я пытаюсь кооперироваться. Эксплуатируем.
        if len(my_history) >= 3 * p:
            my_cycle = my_history[-p:]
            my_expected = my_cycle * 3
            my_actual = my_history[-3 * p :]
            my_periodic = all(a == e for a, e in zip(my_actual, my_expected))
            my_mixed = "C" in my_cycle and "D" in my_cycle
            if my_periodic and my_mixed:
                # Echo-каскад: я тоже зацикливаюсь со смесью C/D.
                # Сбросим попыткой C.
                continue
        return "D"

    # Не периодический → TF2T для постоянной защиты от echo.
    if opp_history[-1] == "D" and opp_history[-2] == "D":
        return "D"
    return "C"
