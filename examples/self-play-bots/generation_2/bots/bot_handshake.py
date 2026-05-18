"""Handshake — стратегия с «секретным рукопожатием» для опознания
своих.

### Идея

Все стратегии, выигравшие в TFT-эпохе турнира, разделяют общую
проблему: они одинаково ведут себя в первых ходах со ВСЕМИ соперниками.
Это значит, что у них **нет способа отличить «своего» от «чужого»**
и переключиться в особо-кооперативный режим без риска быть
эксплуатируемым.

Handshake решает это через **секретную сигнатуру** в первых 5 ходах:

| Раунд | Ход |
|-------|-----|
| 0     | D   |
| 1     | C   |
| 2     | D   |
| 3     | C   |
| 4     | C   |

Сигнатура DCDCC выбрана так, что её **не воспроизводят** случайно
известные стратегии в пантеоне:

- AllC = CCCCC (matches 1,3,4 = 3/5, не проходит порог ≥4)
- AllD = DDDDD (matches 0,2 = 2/5)
- TFT vs HS = CDCDC (matches 4 = 1/5)
- cTFT vs HS = CDCDC (то же, 1/5)
- TF2T vs HS = CCDCC (matches 1,2,3,4 = 4/5! почти проходит,
  но в 4 позиции у TF2T C, у нас C — да, matches; в позиции 2
  TF2T C, у нас D — mismatch. Итого 3/5 в типичном случае).
- SM vs HS = считает: r0 (нет истории, default C), r1 (HS=D, SM
  c=0, d=1, играет D), r2 (HS=C, SM c=1, d=1, играет C), r3 (HS=D,
  SM c=2, d=1, C), r4 (HS=C, c=3, d=1, C) → CDCCC, matches r0(C≠D),
  r1(D≠C), r2(C=D? нет C, нет D), r3(C≠C... wait). Это 1-2/5.
- Random = 50/50, P(≥4/5 match) = (5+1)/32 = 18.75%. Это
  принимается как контролируемый риск; vs Random мы получим
  ~290 (CC × 50% = 1.5 за раунд) при опознании = чистая
  потеря ~150 очков с вероятностью 0.19 → -29 очков среднего
  от vs Random. Но это не критично.

После раунда 5 — проверка:

- Если `opp_history[0:5]` совпадает с сигнатурой в ≥4 позициях →
  **comrade-mode**: играем C, но защищаемся от «маски-handshake»
  через TFT-фолбэк на ≥2 D у соперника в окне 5.
- Иначе → **cTFT-mode** (стандартный contrite TFT).

### Чем это лучше cTFT для популяции с handshake-копиями

В матче handshake vs handshake обе стороны играют DCDCC, после
раунда 5 опознают друг друга → играют CC до конца → ~595 очков
(плюс штраф ~0-2 за шум). Это **выше**, чем cTFT vs cTFT (~590),
что и есть «эволюционный бонус клана».

В матчах с не-handshake-ами — handshake играет первые 5 ходов
«за свой счёт» (теряет ~5-8 очков относительно cTFT vs TFT),
затем стандартный cTFT. Чистая потеря: ~3-5 очков среднего.

### Прогноз

- vs HS (self-play): ~590 (CC после раунда 5)
- vs cTFT: ~510 (первые 5 ходов хуже, чем cTFT vs cTFT; затем CC)
- vs TFT: ~480 (TFT каскадирует на наши probe-D, cTFT-фолбэк
  восстанавливает)
- vs AllC: ~600 (CC × 195 + штраф от probe-DD; AllC не отвечает на D)
- vs AllD: ~210 (после probe TFT-зеркало, как у TFT)
- vs Grim: ~213 (первое D в раунде 0 триггерит Grim в AllD навсегда)
- vs classifier: ~?? — classifier тоже играет DD в первых ходах,
  поэтому opp_history[0:5] = DDC??. С нашим DCDCC matches:
  r0(D=D)+r3(C=C если у classifier C)+r4(C=C если C) = 3-4/5.
  Если 4 — мы ошибочно опознаем classifier как handshake и
  кооперируем; classifier нас экспериментирует не на AllC (мы
  не AllC после probe), и попадает в cTFT-фолбэк. Это похоже на
  cTFT vs classifier ~590.

Главный вопрос: сколько «своих» в популяции?
В T14 будет только один handshake. Self-play бонус — один матч из 17,
~+5 очков среднего относительно cTFT-без-handshake. Этого
**не хватит** для топ-3 (зазор между cTFT и плато сейчас ~10-15).

### Реальный мир

- **Масонство и тайные общества** — рукопожатия, специальные слова,
  ритуальные обмены для опознания своих.
- **Shibboleth (Judges 12)** — произношение слова отличало эфраимитов
  от галаадитов; неправильное произношение — смерть.
- **Гангстерские татуировки, цвета банд** — публичная сигнатура
  принадлежности к клану.
- **«Friend of Dorothy?»** — кодовая фраза в pre-Stonewall LGBT
  для безопасного опознания.
- **Академические сети цитирования** — «правильные» цитаты в начале
  работы сигнализируют о принадлежности к школе.
- **Дипломатические протоколы** — формальные приветствия, тосты,
  ритуалы для опознания «своих» дипломатов.
- **Brand loyalty** — Apple users vs PC users; tribes within
  ecosystems.

Во всех этих случаях handshake-механика **снижает риск
эксплуатации в группе своих** ценой потери возможностей с
аутсайдерами. Это **базовый механизм формирования коалиций**.
"""

# Секретная сигнатура: D, C, D, C, C
SIGNATURE = ("D", "C", "D", "C", "C")
SIG_LEN = len(SIGNATURE)
# Порог опознания: минимум 4 из 5 позиций должны совпасть.
RECOGNIZE_THRESHOLD = 4


def _ctft_move(my_history, opp_history):
    """Стандартный contrite TFT (как в bot_contrite_tft)."""
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
        # Свой опознан. Играем кооперативно, но защищаемся от
        # «маскированного» хищника через окно: если соперник в
        # последних 5 ходах сыграл ≥2 D — переходим в TFT-зеркало.
        recent = opp_history[-5:]
        if recent.count("D") >= 2:
            return "D" if opp_history[-1] == "D" else "C"
        return "C"
    # Чужой — стандартный contrite TFT.
    return _ctft_move(my_history, opp_history)
