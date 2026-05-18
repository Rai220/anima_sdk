"""Adaptive Hardener — gTFT с фазовым переключением hard-D / soft-gTFT.

Мотивация (T20 анализ):
  gTFT-база (включая `bot_adaptive_defender` и сам `bot_generous_tft`)
  теряет ~150 очков на матчах против AllD-семьи:
  - gTFT vs AllD = 139 vs 486 (gTFT прощает 1/3 → AllD доит дальше).
  - gTFT vs Grim = 179 vs 466 (один шум → DD навсегда, gTFT всё ещё прощает).
  - gTFT vs Gradual = 260 vs 498 (Gradual каскадно наказывает).

  В T20 #3-5 заняли gTFT/Omega/a-gTFT — все теряют здесь. Adaptive
  Defender добавил спец-детектор Prober, но **общая проблема "слишком
  мягкая база"** осталась.

  a-gTFT решает это глобальным порогом opp_C < 0.35 → AllD. Но:
  - Глобальная доля медленно сходится (нужно ~20 раундов).
  - Необратимо: даже если соперник "одумается", a-gTFT в hostile.

Гипотеза Hardener: использовать **скользящее окно (window=10)** для
быстрой реакции + **обратимость** для шумовой устойчивости.

Алгоритм:

  Состояние выводится из history (бот stateless):
  - n = len(my_history).
  - n == 0 → C (первый ход, nice).
  - n < 4   → C (warmup, не классифицируем по 1-3 ходам).
  - Считаем opp_d_recent = opp_history[-10:].count("D") (или меньше окно).
  - Считаем opp_streak_d = длина текущей цепочки D в opp_history с конца.

  Триггер hard-mode:
    - opp_d_recent >= 7 (т.е. >=70% D в окне 10), ИЛИ
    - opp_streak_d >= 5 (5 подряд D от соперника).

  В hard-mode → D. С одной оговоркой: если последние 3 хода соперника
  были все C (попытка примирения), выходим из hard-mode → возвращаемся
  к gTFT. Это и есть «обратимость».

  Если не hard-mode → gTFT (g=1/3).

Почему это отлично от существующих:

  - **a-gTFT**: глобальная доля, не window. a-gTFT не реагирует
    быстро на смену поведения. Hardener реагирует за 5-10 раундов.
  - **Omega TFT**: переключается необратимо после 8 неоправданных D.
    Hardener может вернуться в кооперацию, если соперник одумался.
  - **Grim**: 1 D → AllD навсегда. Hardener не триггерится одиночным
    шумовым D (нужно 7 в окне 10 или 5 подряд).
  - **Adaptive AllC**: триггер opp_d >=5, abs+rate, необратимо.
    Hardener — обратимый, на window-статистике.

Ожидаемые матчи:

  vs AllD: opp_streak_d=5 к раунду 5 → hard mode. Все опп ходы — D,
    значит "примирение" не сработает. Hard mode до конца. Очки ≈ 200.

  vs Grim: после первого моего шумового D (вероятность ~0.02 на ход
    за 200 раундов ≈ 98% что хоть один шум будет) → Grim в D навсегда.
    Streak detector ловит. Hard mode. Очки ≈ 195 (paritет DD).
    Сильно лучше gTFT (179).

  vs Gradual: Gradual в фазе punishment играет каскад D. Detector
    ловит. Hard mode → D. Я не получу T=5 от Gradual в фазе calm
    (т.к. в hard mode). Но и не теряю каскад. Очки ≈ 200-250.

  vs AllC: opp_d_recent ≈ 0 (только от шума, ~0.2 в окне). Не
    триггерится. Я в gTFT → высокая CC. Очки ≈ 575-590.

  vs TFT: opp_d ≈ моя D-доля (мои шумовые D + редкие cascade). Если
    я не шумлю, opp_d ≈ 0.02. Не триггерится. CC. ≈ 580-595.

  vs Tester (D,C,D,C,...): opp_d в окне ≈ 0.5. Не >= 7. Streak D = 1.
    Не триггерится. → gTFT vs Tester ≈ 400.

  vs Pavlov: Pavlov переключается после S/P. После моего шумового D
    Pavlov в D, ловит P=1, переключается обратно в C. opp_streak_d
    обычно 1-2. Не триггерится. → gTFT vs Pavlov.

  vs Random: opp_d_recent ≈ 0.5. Не >= 7 (нужно ровно 7+ из 10).
    Иногда триггерится по случаю. → mix of gTFT and hard-D.

  vs self (другой Hardener): чистое CC, или после редкого шума —
    короткий каскад → "примирение" через 3 C → возврат. Очки ≈ 580.

Цена обратимости:

  - Если соперник 5 раз D, потом 3 раза C, потом снова 5 раз D — буду
    качаться между hard и soft. На длинном горизонте это плохо
    (теряю T=5 от "выходных" C). Это **сознательная цена за
    шумовую устойчивость**.

  - Возможна жертва раунда: после exit-из-hard я играю C (gTFT база),
    а соперник снова D → потеря 5 за раунд. Но это редко.

Связь с реальностью:

  - **Санкции с пересмотром**: ЕС/США вводят санкции против страны,
    но регулярно пересматривают их при «улучшении поведения». Это
    обратимое наказание, а не Grim навсегда.
  - **Условное освобождение**: преступник наказан, но при хорошем
    поведении может вернуться в общество. Не один и навсегда.
  - **Психотерапия пар**: после серии конфликтов терапевт может
    рекомендовать «период холода» (hard mode), потом тестовое
    сближение (probe). При успехе — возврат к нормальной коммуникации.
  - **Антимонопольное право**: компании-нарушители получают штрафы и
    ограничения, но при доказанном изменении поведения — возврат
    к нормальному режиму.

Аксельродовы принципы:

  - nice ✓ (первый ход — C).
  - retaliatory ✓ (hard mode на устойчивый паттерн D).
  - forgiving ✓ (3 C от соперника → выход из hard mode).
  - non-envious ✓ (в hard mode паритет DD, в soft mode оба получают R).
"""

import random

_rng = random.Random()

GENEROSITY = 1.0 / 3.0
WINDOW = 10
TRIGGER_D_COUNT = 7
TRIGGER_STREAK = 5
RECOVERY_C_COUNT = 3  # сколько подряд C от соперника, чтобы выйти из hard


def _opp_streak_d(opp_history):
    """Длина текущей цепочки D в opp_history с конца."""
    streak = 0
    for mv in reversed(opp_history):
        if mv == "D":
            streak += 1
        else:
            break
    return streak


def _opp_streak_c(opp_history):
    """Длина текущей цепочки C в opp_history с конца."""
    streak = 0
    for mv in reversed(opp_history):
        if mv == "C":
            streak += 1
        else:
            break
    return streak


def _in_hard_mode(my_history, opp_history):
    """Решить, должны ли мы быть в hard mode сейчас.

    Логика обратимости: hard включается, когда видим устойчивый
    паттерн D (окно или streak), и выключается, когда видим
    RECOVERY_C_COUNT подряд C от соперника.
    """
    n = len(opp_history)
    if n < 4:
        return False

    # Если соперник только что показал устойчивую кооперацию —
    # выходим из hard mode независимо от старой статистики.
    if _opp_streak_c(opp_history) >= RECOVERY_C_COUNT:
        return False

    # Окно: считаем D в последних WINDOW ходах.
    window = opp_history[-WINDOW:] if n >= WINDOW else opp_history
    opp_d_recent = window.count("D")
    if opp_d_recent >= TRIGGER_D_COUNT:
        return True

    # Streak: 5 подряд D — hard mode даже если окно ещё короткое.
    if _opp_streak_d(opp_history) >= TRIGGER_STREAK:
        return True

    return False


def choose_move(my_history, opp_history):
    n = len(opp_history)
    if n == 0:
        return "C"

    # Warmup: первые 4 хода — нежная gTFT-кооперация без классификации.
    if n < 4:
        if opp_history[-1] == "C":
            return "C"
        # На раннем D — прощаем с p=1/3.
        return "C" if _rng.random() < GENEROSITY else "D"

    # Hard mode по window/streak.
    if _in_hard_mode(my_history, opp_history):
        return "D"

    # Иначе — обычный gTFT.
    if opp_history[-1] == "C":
        return "C"
    return "C" if _rng.random() < GENEROSITY else "D"
