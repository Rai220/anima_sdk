"""Classifier — короткая фаза разведки + olive-branch + cTFT-фолбэк.

Идея: первые два хода — D (probe), потом несколько ходов C
(olive branch), потом cTFT-логика для всего остального.
Классификатор смотрит на **отклик соперника на наши D** (opp_history[1]
и opp_history[2]) и решает, является ли соперник «наивным
кооператором» (AllC), которого можно эксплуатировать.

### Phase diagram

| Раунд      | Поведение                                      |
|------------|------------------------------------------------|
| 0, 1       | Probe: играем `D`                              |
| 2          | Olive: играем `C` (пока ждём opp_history[2])   |
| 3..6       | Olive: играем `C`, либо `D` если naive         |
| 7+         | cTFT (с олив-бранч и alt-deadlock-break)      |

### Классификация на раунде 3

При `n >= 3` мы видим **отклики соперника на наши probe-D**:

- `opp_history[1]` — ответ соперника на наш D в раунде 0.
- `opp_history[2]` — ответ на наш D в раунде 1.

Если оба отклика = C (соперник **не отомстил** ни на один наш D), и
шум не перевернул наши probe-D в C, классифицируем соперника как
**AllC-naive** и переходим в эксплуатацию (`D` навсегда).

Иначе — соперник реактивный, продолжаем olive (рауンды 3..6), затем
переходим в cTFT.

### Защита от noise

Если шум перевернул хотя бы один из наших probe-D в C, не можем
надёжно классифицировать соперника по этому пробнику — соперник не
получил сигнала. Поэтому проверяем `my_history[probe_idx] == 'D'`
прежде чем учитывать `opp_history[probe_idx + 1]` как отклик. Если
оба пробника «не прошли» — `probe_resps` пуст или содержит < 2
элементов → не классифицируем как naive → дефолтный olive+cTFT.

Цена: ~0.04 вероятность того, что хотя бы один пробник перевернётся,
тогда vs AllC мы получим ~600 (CC) вместо ~990 (exploit). Ожидаемая
потеря: 0.04 × 390 ≈ 16 очков по матчу. Приемлемо.

### Olive branch (раунды 2..6)

После probe-D наша CC-кооперация с TF2T/TFT/cTFT/SM поломана: они
видят `[D, D]` в opp_history и переключаются в D-режим. Чтобы выйти
из CD-каскада, мы безусловно играем C на ~5 раундов после probe.

- **TFT**: после моего D в раунде 1, в раунде 2 играет D. Я играю C.
  В раунде 3 TFT видит мой C → играет C. Возвращение в CC.
- **TF2T**: в раунде 2 видит `[D, D]` → играет D. Я играю C. В раунде
  3 TF2T видит `[D, D, C]` → последние 2 не оба D → играет C. CC.
- **SM**: в раундах 2-3 у меня c=0, d=2 → SM играет D. На раунде 4
  у меня c=2, d=2 (равенство) → SM играет C. Возврат в CC на раунде 5.
- **cTFT**: на раунде 2 видит `[D]` (только opp_history[1]), играет
  D (TFT-зеркало). На раунде 3 видит `[D, D]` (TFT каскад). На раунде
  4 видит `[D, D, C]` — мой C даёт ему сигнал прощения. Прощает на 5.
- **Pavlov**: после probe Pavlov в DD-цикле, чередует ходы. После
  моей C-цепочки попадает в (D, C) → T=5 → стабилизируется в D.
  Мы играем olive C × 5 → Pavlov играет DC...DC → нам S=0 х много.
  Потом cTFT vs Pavlov-как-в-T12.

### cTFT-фолбэк (с олив-бранч из omega-TFT)

Стандартный cTFT-логика не справляется с длинными DD-trap (см.
анализ T12). Поэтому в фолбэке используем версию из omega-TFT с
двумя дополнительными «деадлок-разрывами»:

1. CDCD-alternation на 4 ходах → играем C.
2. DDDD на 3 ходах при доле моих D < 0.40 → играем C.

Это даёт **+50 очков vs TFT** по сравнению с чистым cTFT.

### Прогноз (с улучшениями)

| Соперник     | cTFT (Т12) | classifier (v4) |
|--------------|-----------:|----------------:|
| AllC         |     591    |    ~960 (exploit)|
| AllD         |     201    |    ~210         |
| Random       |     441    |    ~450         |
| TFT          |     530    |    ~580 (после olive восстановление) |
| Grim         |     389    |    ~210 (probe триггерит Grim в AllD) |
| Pavlov       |     474    |    ~480         |
| TF2T         |     595    |    ~590 (после olive восстановление) |
| gTFT         |     580    |    ~580         |
| cTFT         |     595    |    ~590         |
| FBF          |     580    |    ~560 (probe-D триггерит FBF-цикл) |
| SM           |     599    |    ~590 (olive восстанавливает)        |
| gradual      |     564    |    ~450 (probe-D в gradual триггерит каскад) |
| omega        |     605    |    ~580         |
| armored      |     583    |    ~560         |
| soft_armored |     598    |    ~580         |
| apavlov      |     463    |    ~470         |
| Self         |       -    |    ~590         |

Ожидаемое среднее: ~530-540 (vs cTFT 521 → +10 average, может пробить
плато топ-3 за счёт +400 vs AllC).

### Главная гипотеза

Существующее плато 510-528 — это все стратегии, **никогда не
получающие T = 5** от наивного кооператора. Бот, который умеет
эксплуатировать AllC, **в одном матче** получает +400 очков. /16
≈ +25 очков среднего. Это должно пробить плато.

Цена: ~10-20 очков потери в матчах vs Grim, vs gradual, vs FBF
(probe-D триггерит их защитные каскады). Чистый прирост ожидаемо
~+10 очков среднего.

### Связь с реальным миром (см. предыдущие версии комментариев)

**Эксплуатация наивных** — это **базовая хищническая стратегия** в
популяциях. Социум защищает себя от классификаторов через:

- **Институциональное доверие** (репутация, подписи, контракты),
  которое нельзя «протестировать» лёгким пробником.
- **Сети защитников** (см. омерта, профсоюзы, государства), которые
  отвечают за наивных как за самих себя.
- **Запрет первого D** (моральные нормы, юр-уставы, soft law). Без
  таких норм AllC-стратегии не могли бы выжить в принципе.

В IPD-турнире нет институтов — каждый сам за себя. Поэтому AllC
доминируется любым агрессором. Однако **разумные общества** строят
институты так, чтобы наивная кооперация была защищена. Это —
**эволюция альтруизма через систему**.
"""

PROBE = 2
ANALYZE_AT = 3
OLIVE_END = 7  # рауンды 2..6 — olive (если не naive)
WIN = 20
D_RATE_LIMIT = 0.70
ALT_WIN = 4
OLIVE_WIN = 3
MUTUAL_D_LIMIT = 0.40


def _ctft_move(my_history, opp_history):
    """cTFT + alt-deadlock + mutual-D olive (как в omega-TFT)."""
    if not opp_history:
        return "C"
    n = len(opp_history)

    # Alternation deadlock (CDCD-DCDC)
    if n >= ALT_WIN:
        my_w = my_history[-ALT_WIN:]
        opp_w = opp_history[-ALT_WIN:]
        is_alt = all(my_w[k] != opp_w[k] for k in range(ALT_WIN))
        my_alt = all(my_w[k] != my_w[k - 1] for k in range(1, ALT_WIN))
        opp_alt = all(opp_w[k] != opp_w[k - 1] for k in range(1, ALT_WIN))
        if is_alt and my_alt and opp_alt:
            return "C"

    # Mutual-D trap (olive branch)
    if n >= OLIVE_WIN:
        my_w = my_history[-OLIVE_WIN:]
        opp_w = opp_history[-OLIVE_WIN:]
        if all(m == "D" for m in my_w) and all(o == "D" for o in opp_w):
            my_d_rate = my_history.count("D") / n
            if my_d_rate < MUTUAL_D_LIMIT:
                return "C"

    # cTFT (contrite-TFT)
    last_opp = opp_history[-1]
    if last_opp == "C":
        return "C"
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


def choose_move(my_history, opp_history):
    n = len(my_history)

    # --- Probe phase (рауンды 0, 1) -------------------------------------------
    if n < PROBE:
        return "D"

    # --- Naive classification (n >= ANALYZE_AT = 3) ---------------------------
    # Соберём отклики соперника на наши *фактически сыгранные* probe-D.
    if n >= ANALYZE_AT:
        probe_resps = []
        for probe_idx in range(PROBE):
            if my_history[probe_idx] == "D":  # probe не перевернулся шумом
                resp_idx = probe_idx + 1
                if resp_idx < n:
                    probe_resps.append(opp_history[resp_idx])

        if len(probe_resps) >= 2 and all(r == "C" for r in probe_resps):
            return "D"  # AllC-naive → эксплуатируем

    # --- AllD-детектор --------------------------------------------------------
    if n >= WIN:
        recent_d = sum(1 for x in opp_history[-WIN:] if x == "D")
        if recent_d >= int(D_RATE_LIMIT * WIN):
            return "D"

    # --- Olive branch (рауンды PROBE..OLIVE_END-1 = 2..6) ---------------------
    if n < OLIVE_END:
        return "C"

    # --- cTFT-фолбэк ----------------------------------------------------------
    return _ctft_move(my_history, opp_history)
