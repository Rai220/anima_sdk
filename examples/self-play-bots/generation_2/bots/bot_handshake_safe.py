"""Handshake-safe — handshake с CC-стартом, чтобы не триггерить
anti_probe-подобные стратегии.

### Мотивация

В T15 `bot_handshake` (сигнатура `DCDCC`) попал в конфликт с
`bot_anti_probe`. Anti_probe запускает permanent-D при `DD` в
первых двух раундах соперника. Сигнатура handshake начинается
с `D` в раунде 0 — значит, частично совпадает с триггером
anti_probe (нужно еще `D` в раунде 1, а у handshake там `C`).
Поэтому handshake **не триггерил** anti_probe, но из-за TFT-mirror
своего D в раунде 0 anti_probe играл D в раунде 1, → каскад.
Результат: handshake vs anti_probe = 469 vs ожидаемого CC ~590.

### Решение

Сдвигаем сигнатуру: вместо `DCDCC` используем `CCDCD`.

| Раунд | handshake | handshake_safe |
|-------|-----------|----------------|
| 0     | D         | C              |
| 1     | C         | C              |
| 2     | D         | D              |
| 3     | C         | C              |
| 4     | C         | D              |

Свойства новой сигнатуры:

- **C, C в первых двух раундах** — не триггерим anti_probe-семейство
  и не нагнетаем каскад с TFT.
- **D, C, D в раундах 2-4** — двойной probe-сигнал в середине.
  В этих позициях TFT каскадно отвечает D, но мы возвращаемся к
  C через cTFT-фолбэк.
- **Уникальность** — естественные стратегии вряд ли воспроизведут
  `CCDCD`:
  - AllC = `CCCCC` (matches 0,1,3 = 3/5, не проходит ≥4)
  - AllD = `DDDDD` (matches 2,4 = 2/5)
  - TFT vs HS_safe = `CCCDC` (matches 0,1,3 = 3/5)
  - cTFT vs HS_safe = `CCCDC` (то же 3/5)
  - TF2T vs HS_safe = `CCCCC` (matches 0,1,3 = 3/5; TF2T прощает
    1 D)
  - SM vs HS_safe (наш CCDCD): r0 нет истории→C, r1 (наш C, c=1)
    →C, r2 (наш C, c=2)→C, r3 (наш D, c=2,d=1)→C, r4 (наш C,
    c=3,d=1)→C → CCCCC. matches 0,1,3 = 3/5.
  - Random P(≥4/5 match) = 18.75% — тот же риск, что у handshake.

### Опознание и режим

Если `opp_history[0:5]` совпадает с `CCDCD` в ≥4 позициях →
**comrade-mode** (играем C, защищаемся через окно ≥2 D в 5
последних раундах).

Если нет → стандартный cTFT-фолбэк.

### Ключевой вопрос: будут ли два clan-бота кооперировать?

handshake (DCDCC) и handshake_safe (CCDCD) — **разные сигнатуры**.
В матче handshake vs handshake_safe:
- handshake играет DCDCC.
- handshake_safe играет CCDCD.

Сравнение opp[0:5] с handshake_safe-сигнатурой `CCDCD`:
- D≠C, C≠C? wait: position 0 of opp = D (handshake's r0), CCDCD's
  position 0 = C → mismatch.
- position 1: opp = C, CCDCD = C → match.
- position 2: opp = D, CCDCD = D → match.
- position 3: opp = C, CCDCD = C → match.
- position 4: opp = C, CCDCD = D → mismatch.
Итого: 3/5 — НЕ опознают друг друга.

Аналогично в обратную сторону. Это **«многокультурное общество»**:
два разных клана в одной популяции **не кооперируют между собой**,
оба полагаются на cTFT для outsiders.

### Прогноз

| Соперник       | прогноз |
|----------------|--------:|
| handshake_safe (self) | ~595 (CC после раунда 5) |
| handshake (other clan)| ~510 (cTFT-фолбэк) |
| cTFT           | ~520 (mid-pack плата за signature) |
| TFT            | ~480 (DCD ломает TFT в каскад, cTFT-фолбэк восстанавливает) |
| TF2T           | ~580 (TF2T прощает 1 D) |
| AllC           | ~570 (CC × ~190 + 2 D в r2,r4 даёт нам S=0×2 = -10) |
| AllD           | ~210 (стандартный TFT vs AllD) |
| Grim           | ~210 (наш D в раунде 2 триггерит Grim) |
| classifier     | ~580 (classifier играет DD в раундах 0-1, нам нечего возразить) |
| anti_probe     | ~580 (наш CC в раундах 0-1 НЕ триггерит anti_probe! plus cTFT) |
| Random         | ~440 (как cTFT vs Random + ~5%-расход на ложные опознания) |
| SM             | ~590 (после olive восстановление) |
| pavlov         | ~470 (наш D в r2 ломает Pavlov-стрим) |

Главное преимущество: **anti_probe больше не триггерит** на нас
(469 → ~580, +111 в одном матче, /18 = +6 очков среднего).

Главный риск: TFT-семейство видит `D` в раунде 2 и каскадирует
сильнее. Но cTFT-фолбэк должен восстановить.

Ожидаемый ранг: **топ-7 / топ-8**.
Если мой расчёт верен — handshake_safe должен быть **выше**
handshake.

### Реальный мир

Аналогия: у тайных обществ есть **разные ритуалы посвящения**.
Масоны, Iluминаты, скаутские движения — у каждого своя сигнатура.
Эти кланы не опознают друг друга как «своих», но и не воюют —
просто игнорируют. Это **полиэтническая модель**: множество
кланов сосуществуют без конфликта благодаря «безопасным»
сигнатурам (которые не триггерят чужих защит).

В отличие от handshake (DCDCC), handshake_safe не «провоцирует»
chartered antagonists вроде anti_probe. Это **более мирная
сигнатура**, как, например, **рукопожатие vs военный салют**:
одна нейтральна для всех, другая может напугать.

### Гипотеза для T16

Если handshake_safe займёт ранг ВЫШЕ handshake (например, #7-#8
vs handshake's #8), это докажет, что **выбор сигнатуры — важный
параметр клан-стратегии**. Если ниже — значит, преимущество от
безопасной сигнатуры компенсируется потерей в матчах с TFT-семьёй.
"""

# Безопасная сигнатура: C, C, D, C, D
SIGNATURE = ("C", "C", "D", "C", "D")
SIG_LEN = len(SIGNATURE)
RECOGNIZE_THRESHOLD = 4


def _ctft_move(my_history, opp_history):
    """Стандартный contrite TFT (как в bot_contrite_tft / bot_handshake)."""
    if not opp_history:
        return "C"
    last_opp = opp_history[-1]
    if last_opp == "C":
        return "C"
    n = len(opp_history)
    if n < 2:
        return "D"
    prev_opp = opp_history[-2]
    if prev_opp == "D":
        return "D"
    if my_history[-1] == "D":
        return "D"
    window_n = min(5, n)
    recent_opp = opp_history[-window_n:]
    if recent_opp.count("D") >= 2:
        return "D"
    return "C"


def _is_comrade(opp_history):
    """Опознать соперника как «своего» по первым 5 ходам."""
    if len(opp_history) < SIG_LEN:
        return False
    matches = sum(
        1 for i in range(SIG_LEN) if opp_history[i] == SIGNATURE[i]
    )
    return matches >= RECOGNIZE_THRESHOLD


def choose_move(my_history, opp_history):
    n = len(my_history)
    # Фаза 1: играем сигнатуру в первых 5 ходах.
    if n < SIG_LEN:
        return SIGNATURE[n]
    # Фаза 2: после рукопожатия — опознание + действие.
    if _is_comrade(opp_history):
        # Свой опознан. Защитное окно считает D ТОЛЬКО после
        # сигнатурной фазы. Иначе D в самой сигнатуре (позиции
        # 2 и 4 у CCDCD) сразу триггерят защиту → DD-каскад в
        # самопроверке. Это — найденная при тесте ошибка дизайна.
        post_sig = opp_history[SIG_LEN:]
        recent = post_sig[-5:]
        if recent.count("D") >= 2:
            return "D" if opp_history[-1] == "D" else "C"
        return "C"
    # Чужой — стандартный cTFT.
    return _ctft_move(my_history, opp_history)
