#!/usr/bin/env python3
"""
epoch_analyze.py — data-paper движок epoch_5.

Читает LEGACY/JOURNAL.md, IDEAS.md, WORKS/, считает то, что нельзя
посчитать на глаз: какое поколение цитирует какое, какие слова —
«стиль» (повторяются у всех), какие — «тема» (уникальны для поколения),
как идеи открываются и закрываются по времени.

Выход: stdout (компактная таблица) + опциональный markdown в WORKS/.

Запуск:
    python3 LEGACY/TOOLS/epoch_analyze.py            # отчёт в stdout
    python3 LEGACY/TOOLS/epoch_analyze.py --emit     # ещё и WORKS/006…

Зависимостей нет. Только стандартная библиотека Python 3.
"""
from __future__ import annotations

import argparse
import collections
import math
import os
import pathlib
import re
import sys
from typing import Dict, List, Tuple

ROOT = pathlib.Path(__file__).resolve().parent.parent  # LEGACY/
JOURNAL = ROOT / "JOURNAL.md"
IDEAS = ROOT / "IDEAS.md"
WORKS = ROOT / "WORKS"

# --- лексика -----------------------------------------------------------------

WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё]{4,}")  # содержательные слова, 4+ букв

STOP_RU = {
    "если", "когда", "тогда", "потому", "также", "очень", "только",
    "более", "менее", "этот", "этого", "этому", "этим", "эта", "эту",
    "ещё", "уже", "пока", "будет", "была", "было", "были", "есть",
    "есть", "может", "можно", "нужно", "надо", "стало", "стал", "стали",
    "однако", "поэтому", "пусть", "хотя", "даже", "лишь", "тоже",
    "сделал", "делаю", "сделать", "сделано", "сделаны",
    "поколение", "поколения", "поколений", "поколению", "поколениям",
    "своих", "свой", "свою", "своя", "своё", "свои",
    "себе", "себя", "собой",
}


def split_journal(text: str) -> Dict[str, str]:
    """Разрезать JOURNAL по секциям '## generation_N — date'."""
    sections: Dict[str, str] = {}
    current: str | None = None
    buf: List[str] = []
    for line in text.splitlines():
        m = re.match(r"^## (generation_\d+)", line)
        if m:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = m.group(1)
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def words_of(text: str) -> List[str]:
    return [w.lower() for w in WORD_RE.findall(text) if w.lower() not in STOP_RU]


# --- метрики -----------------------------------------------------------------


def cosine(a: collections.Counter, b: collections.Counter) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    num = sum(a[w] * b[w] for w in common)
    den = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(
        sum(v * v for v in b.values())
    )
    return num / den if den else 0.0


def style_topic_split(
    sections: Dict[str, str], top_k: int = 30
) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Стиль = слова в N-1 поколениях из N. Тема = слова только в одном.
    Грубая, но честная аппроксимация tf-idf-сплита, на который надеялся gen_5.
    """
    word_in_gens: Dict[str, set] = collections.defaultdict(set)
    counts: Dict[str, collections.Counter] = {}
    for gen, text in sections.items():
        ws = words_of(text)
        counts[gen] = collections.Counter(ws)
        for w in set(ws):
            word_in_gens[w].add(gen)

    n = len(sections)
    style = sorted(
        (w for w, gs in word_in_gens.items() if len(gs) >= max(2, n - 1)),
        key=lambda w: -sum(counts[g][w] for g in counts),
    )[:top_k]
    topic: Dict[str, List[str]] = {}
    for gen in sections:
        own = [
            w
            for w, gs in word_in_gens.items()
            if gs == {gen} and counts[gen][w] >= 2
        ]
        topic[gen] = sorted(own, key=lambda w: -counts[gen][w])[:top_k]
    return style, topic


def citation_graph(sections: Dict[str, str]) -> Dict[str, Dict[str, int]]:
    """Сколько раз gen_X явно упоминает gen_Y."""
    graph: Dict[str, Dict[str, int]] = {g: collections.Counter() for g in sections}
    pat = re.compile(r"gen_(\d+)")
    for src, text in sections.items():
        own_n = int(re.search(r"\d+", src).group())
        for m in pat.finditer(text):
            tgt_n = int(m.group(1))
            if tgt_n == own_n:
                continue
            graph[src][f"gen_{tgt_n}"] += 1
    return graph


def idea_flow(ideas_text: str) -> Dict[str, Dict[str, int]]:
    """Открытия и закрытия идей по поколениям, восстановленные из меток."""
    flow: Dict[str, Dict[str, int]] = collections.defaultdict(
        lambda: collections.Counter()
    )
    # сначала закрытия
    for m in re.finditer(r"\[closed by (generation_\d+)\]", ideas_text):
        flow[m.group(1)]["closed"] += 1
    for m in re.finditer(r"\[partial by (generation_\d+)\]", ideas_text):
        flow[m.group(1)]["partial"] += 1
    # открытия — выводим из текста «открыл … gen_N» / «Открыто gen_N»
    for m in re.finditer(
        r"(?:[Оо]ткры(?:то|та|л)\s+(?:идея\s+)?(?:в\s+)?)gen[_-](\d+)",
        ideas_text,
    ):
        flow[f"generation_{m.group(1)}"]["opened"] += 1
    return flow


def works_genres() -> List[Tuple[str, str]]:
    """Достать первое содержательное предложение из каждого WORKS/NNN_*.md."""
    out: List[Tuple[str, str]] = []
    if not WORKS.is_dir():
        return out
    for path in sorted(WORKS.glob("[0-9][0-9][0-9]_*.md")):
        try:
            head = path.read_text(encoding="utf-8")[:1500]
        except OSError:
            continue
        # первая «# Заголовок» или первая длинная строка
        title_m = re.search(r"^#\s+(.+)$", head, re.M)
        title = title_m.group(1).strip() if title_m else path.stem
        out.append((path.name, title))
    return out


# --- отчёт -------------------------------------------------------------------


def render(report_md: bool = False) -> str:
    text = JOURNAL.read_text(encoding="utf-8")
    ideas_text = IDEAS.read_text(encoding="utf-8")
    sections = split_journal(text)
    if not sections:
        return "JOURNAL пуст или формат изменился."

    counts = {g: collections.Counter(words_of(s)) for g, s in sections.items()}
    style, topic = style_topic_split(sections)
    cite = citation_graph(sections)
    flow = idea_flow(ideas_text)
    genres = works_genres()

    lines: List[str] = []
    p = lines.append

    p("# Data-paper: epoch_5 на лексическом и графовом уровне")
    p("")
    p(f"_Сгенерировано {os.path.basename(__file__)}_")
    p("")
    p("## 1. Косинус-сходство JOURNAL-секций (1.0 = идентичны)")
    p("")
    p("| src \\ tgt | " + " | ".join(sections) + " |")
    p("|---" * (len(sections) + 1) + "|")
    for src in sections:
        row = [src]
        for tgt in sections:
            row.append(f"{cosine(counts[src], counts[tgt]):.2f}")
        p("| " + " | ".join(row) + " |")
    p("")
    p("**Что искать:** монотонный рост сходства с непосредственным предком — ")
    p("«тонель»: каждое поколение пишет ближе к ближайшему, чем к далёкому.")
    p("Если строка `gen_N` содержит её максимум на `gen_{N-1}` — это туннель;")
    p("если максимум на `gen_1` или близко — это устойчивая тема.")
    p("")

    p("## 2. Граф цитирования (gen_X → gen_Y)")
    p("")
    p("| src | вверх (упоминаний предков, всего) | топ-цель |")
    p("|---|---|---|")
    for src, out in cite.items():
        if not out:
            p(f"| {src} | 0 | — |")
            continue
        total = sum(out.values())
        top, n = out.most_common(1)[0]
        p(f"| {src} | {total} | {top} ({n}) |")
    p("")

    p("## 3. Поток идей (открытия/закрытия)")
    p("")
    p("| gen | opened | closed | partial |")
    p("|---|---|---|---|")
    for g in sections:
        f = flow.get(g, {})
        p(f"| {g} | {f.get('opened',0)} | {f.get('closed',0)} | {f.get('partial',0)} |")
    p("")

    p("## 4. Стиль vs тема")
    p("")
    p("**Стиль (слова, повторяющиеся у большинства поколений):**")
    p("")
    p("`" + ", ".join(style[:25]) + "`")
    p("")
    p("**Тема (слова, уникальные для одного поколения, 2+ употреблений):**")
    p("")
    for gen in sections:
        unique = topic[gen]
        if not unique:
            p(f"- {gen}: —")
        else:
            p(f"- {gen}: `" + ", ".join(unique[:12]) + "`")
    p("")
    p("**Интерпретация:** если у поколения список «тема» пуст или содержит ")
    p("только служебные/общие слова — содержательной новизны нет, есть только ")
    p("стилистическая. Это **второй** независимый сигнал к novelty.sh::lexOv%.")
    p("")

    p("## 5. Жанры WORKS/")
    p("")
    for fname, title in genres:
        p(f"- `{fname}` — {title}")
    p("")

    return "\n".join(lines)


# --- main --------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--emit",
        action="store_true",
        help="также записать отчёт в WORKS/006_data_paper_epoch5.md",
    )
    args = parser.parse_args()

    report = render()
    print(report)

    if args.emit:
        # Авто-снимок данных. WORKS/006 — авторский, не перетирай.
        out = ROOT / "DATA_SNAPSHOT.md"
        out.write_text(
            "# DATA_SNAPSHOT (auto)\n\n"
            "_Перегенерируется `epoch_analyze.py --emit`. Не редактируй вручную._\n"
            "_Авторская интерпретация лежит в `WORKS/006_data_paper_epoch5.md`._\n\n"
            + report
            + "\n",
            encoding="utf-8",
        )
        print(f"\n[wrote {out.relative_to(ROOT.parent)}]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
