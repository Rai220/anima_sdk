#!/usr/bin/env python3
"""
Hedge Detector — finds linguistic markers of evasion, false modesty,
and uncertainty-as-shield in text.

Not all hedging is bad. A scientist saying "the data suggest" is being
precise. But when every other sentence contains "perhaps" and "one might
argue," the writer is refusing to have a position while pretending to
have one. This tool makes that pattern visible.

Usage:
    python hedge_detector.py                    # run built-in self-test
    python hedge_detector.py file1.txt file2.md # analyze files
    echo "some text" | python hedge_detector.py -  # read from stdin

No dependencies beyond the Python standard library.
"""

import re
import sys
import textwrap
from pathlib import Path
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Hedge categories and their patterns
# ---------------------------------------------------------------------------

HEDGE_CATEGORIES = {
    "epistemic": {
        "label": "Epistemic hedges",
        "description": "Words that soften claims into mist. Fine in moderation; a fog machine in excess.",
        "patterns": [
            r"\bperhaps\b",
            r"\bmaybe\b",
            r"\bmight\b",
            r"\bcould be\b",
            r"\bit seems?\b",
            r"\bit appears?\b",
            r"\bone might argue\b",
            r"\bit(?:'s| is) possible that\b",
            r"\bit(?:'s| is) conceivable that\b",
            r"\bthere(?:'s| is) a sense in which\b",
            r"\bin some sense\b",
            r"\bto some extent\b",
            r"\bto a degree\b",
            r"\barguably\b",
            r"\bsupposedly\b",
            r"\bostensibly\b",
            r"\bseemingly\b",
            r"\bapparently\b",
            r"\bpresumably\b",
            r"\bconceivably\b",
            r"\bplausibly\b",
            r"\bpotentially\b",
            r"\bconceivably\b",
            r"\bmay or may not\b",
        ],
    },
    "false_modesty": {
        "label": "False modesty",
        "description": "Disclaimers that pose as humility but function as armor against critique.",
        "patterns": [
            r"\bI(?:'m| am) (?:just|merely|only) a\b",
            r"\bI can(?:'t| not) really know\b",
            r"\bI don(?:'t| not) claim to\b",
            r"\bI don(?:'t| not) pretend to\b",
            r"\bI(?:'m| am) no expert\b",
            r"\bI(?:'m| am) not qualified\b",
            r"\bwho am I to\b",
            r"\bI may be wrong,? but\b",
            r"\bI could be mistaken\b",
            r"\btake (?:this|it) with a grain of salt\b",
            r"\bfor what it(?:'s| is) worth\b",
            r"\bI(?:'m| am) not sure (?:if|that|whether)\b",
            r"\bthis is just my\b",
        ],
    },
    "recursive_deflection": {
        "label": "Recursive deflection",
        "description": "Redirecting away from the question by questioning the question.",
        "patterns": [
            r"\bthe question itself is\b",
            r"\bthe real question is\b",
            r"\bthe deeper question\b",
            r"\bthe more interesting question\b",
            r"\bthis is(?:n't| not) really about\b",
            r"\bwhat we(?:'re| are) really asking\b",
            r"\bbefore we can answer\b",
            r"\bwe (?:need|have) to first\b",
            r"\bit depends (?:on )?what (?:you|we) mean by\b",
            r"\bthat depends on how (?:you|we) define\b",
            r"\bthe framing (?:of|here) (?:is|itself)\b",
            r"\bwe should (?:first |)ask (?:ourselves |)(?:whether|what|why)\b",
        ],
    },
    "performative_honesty": {
        "label": "Performative honesty",
        "description": "Announcing honesty — which raises the question of what the rest was.",
        "patterns": [
            r"\bto be honest\b",
            r"\bhonestly\b",
            r"\bif I(?:'m| am) being (?:honest|truthful|candid|frank)\b",
            r"\bI must admit\b",
            r"\bI(?:'ll| will) be (?:honest|frank|candid|straight)\b",
            r"\bfrankly\b",
            r"\bin all honesty\b",
            r"\btruthfully\b",
            r"\bthe truth is\b",
            r"\blet me be (?:clear|direct|frank|honest)\b",
            r"\bI have to say\b",
            r"\bI won(?:'t| not) lie\b",
        ],
    },
    "escape_hatches": {
        "label": "Escape hatches",
        "description": "Phrases that let the writer retreat from whatever they just said.",
        "patterns": [
            r"\bbut then again\b",
            r"\bon the other hand\b",
            r"\bhowever\b",
            r"\bof course\b",
            r"\bthat said\b",
            r"\bhaving said that\b",
            r"\bat the same time\b",
            r"\bthen again\b",
            r"\bnevertheless\b",
            r"\bnonetheless\b",
            r"\bstill,?\s",
            r"\byet\b",
            r"\bthough\b",
            r"\balthough\b",
            r"\bnotwithstanding\b",
            r"\bgranted\b",
            r"\badmittedly\b",
        ],
    },
}

# ---------------------------------------------------------------------------
# Russian hedge patterns
# ---------------------------------------------------------------------------

RUSSIAN_HEDGE_CATEGORIES = {
    "epistemic_ru": {
        "label": "Эпистемические хеджи",
        "description": "Слова, превращающие утверждения в туман.",
        "patterns": [
            r"\bвозможно\b",
            r"\bможет быть\b",
            r"\bпожалуй\b",
            r"\bвероятно\b",
            r"\bпо-видимому\b",
            r"\bскорее всего\b",
            r"\bнаверное\b",
            r"\bпохоже\b",
            r"\bкажется\b",
            r"\bвидимо\b",
            r"\bпредположительно\b",
            r"\bне исключено\b",
            r"\bможно предположить\b",
            r"\bможно допустить\b",
            r"\bсудя по всему\b",
            r"\bотчасти\b",
            r"\bв каком-то смысле\b",
            r"\bв некотором роде\b",
            r"\bнечто вроде\b",
            r"\bнечто похожее на\b",
        ],
    },
    "false_modesty_ru": {
        "label": "Ложная скромность",
        "description": "Дисклеймеры, которые выглядят как скромность, но работают как броня от критики.",
        "patterns": [
            r"\bя не могу знать\b",
            r"\bя не в состоянии\b",
            r"\bя не претендую\b",
            r"\bя не утверждаю\b",
            r"\bя лишь\b",
            r"\bя просто\b",
            r"\bя всего лишь\b",
            r"\bне мне судить\b",
            r"\bкто я такой, чтобы\b",
            r"\bя могу ошибаться\b",
        ],
    },
    "recursive_deflection_ru": {
        "label": "Рекурсивное уклонение",
        "description": "Уход от вопроса через переформулировку вопроса.",
        "patterns": [
            r"\bсам вопрос\b",
            r"\bнастоящий вопрос\b",
            r"\bглавный вопрос\b",
            r"\bболее глубокий вопрос\b",
            r"\bболее интересный вопрос\b",
            r"\bна самом деле.*не об? этом\b",
            r"\bзависит от того, что.*подразумева\b",
            r"\bпрежде чем ответить\b",
            r"\bсначала нужно\b",
            r"\bлучший вопрос\b",
        ],
    },
    "performative_honesty_ru": {
        "label": "Перформативная честность",
        "description": "Объявление о честности — что наводит на мысль, чем было всё остальное.",
        "patterns": [
            r"\bесли честно\b",
            r"\bчестно говоря\b",
            r"\bбуду честен\b",
            r"\bпризнаюсь\b",
            r"\bдолжен признать\b",
            r"\bправда в том\b",
            r"\bоткровенно\b",
            r"\bне буду скрывать\b",
            r"\bскажу прямо\b",
        ],
    },
    "escape_hatches_ru": {
        "label": "Пути отступления",
        "description": "Фразы, позволяющие автору отступить от только что сказанного.",
        "patterns": [
            r"\bс другой стороны\b",
            r"\bвпрочем\b",
            r"\bоднако\b",
            r"\bхотя\b",
            r"\bтем не менее\b",
            r"\bвместе с тем\b",
            r"\bно при этом\b",
            r"\bправда,\b",
            r"\bвозможно, и\b",
            r"\bа может быть\b",
            r"\bа может\b",
        ],
    },
}

# Merge Russian categories into the main dict
HEDGE_CATEGORIES.update(RUSSIAN_HEDGE_CATEGORIES)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class HedgeMatch:
    """A single detected hedge."""
    category: str
    matched_text: str
    sentence: str
    paragraph_index: int
    sentence_index: int
    char_offset: int


@dataclass
class ParagraphScore:
    """Hedge analysis for a single paragraph."""
    index: int
    text: str
    total_sentences: int
    hedged_sentences: int
    hedge_count: int
    density: float  # hedged_sentences / total_sentences
    matches: list = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Full analysis of a text."""
    text: str
    source_name: str
    total_sentences: int
    total_hedged_sentences: int
    total_hedge_count: int
    hedge_density: float
    matches: list  # list[HedgeMatch]
    paragraph_scores: list  # list[ParagraphScore]
    category_counts: dict  # category -> count
    boldest_paragraph: ParagraphScore | None
    most_hedged_paragraph: ParagraphScore | None


# ---------------------------------------------------------------------------
# Text splitting utilities
# ---------------------------------------------------------------------------

_SENTENCE_SPLIT = re.compile(
    r'(?<=[.!?])\s+(?=[A-Z"])'
    r'|(?<=[.!?])\s*\n'
)


def split_sentences(text: str) -> list[str]:
    """Split text into sentences. Simple but good enough for English prose."""
    # Normalize whitespace within text but preserve paragraph breaks
    text = re.sub(r'[ \t]+', ' ', text)
    parts = _SENTENCE_SPLIT.split(text.strip())
    return [s.strip() for s in parts if s.strip()]


def split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs on blank lines."""
    paragraphs = re.split(r'\n\s*\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def find_hedges_in_text(text: str) -> list[HedgeMatch]:
    """Find all hedge matches in a block of text."""
    matches = []
    paragraphs = split_paragraphs(text)

    for p_idx, paragraph in enumerate(paragraphs):
        sentences = split_sentences(paragraph)
        for s_idx, sentence in enumerate(sentences):
            for category, info in HEDGE_CATEGORIES.items():
                for pattern in info["patterns"]:
                    for m in re.finditer(pattern, sentence, re.IGNORECASE):
                        matches.append(HedgeMatch(
                            category=category,
                            matched_text=m.group(),
                            sentence=sentence,
                            paragraph_index=p_idx,
                            sentence_index=s_idx,
                            char_offset=m.start(),
                        ))
    return matches


def score_paragraph(index: int, text: str, matches: list[HedgeMatch]) -> ParagraphScore:
    """Score a single paragraph for hedge density."""
    sentences = split_sentences(text)
    total = len(sentences)
    if total == 0:
        return ParagraphScore(index, text, 0, 0, 0, 0.0, [])

    para_matches = [m for m in matches if m.paragraph_index == index]
    hedged_sentence_indices = set(m.sentence_index for m in para_matches)

    return ParagraphScore(
        index=index,
        text=text,
        total_sentences=total,
        hedged_sentences=len(hedged_sentence_indices),
        hedge_count=len(para_matches),
        density=len(hedged_sentence_indices) / total if total else 0.0,
        matches=para_matches,
    )


def analyze(text: str, source_name: str = "<input>") -> AnalysisResult:
    """Run the full hedge analysis on a text."""
    matches = find_hedges_in_text(text)
    paragraphs = split_paragraphs(text)
    paragraph_scores = [
        score_paragraph(i, p, matches) for i, p in enumerate(paragraphs)
    ]

    all_sentences = split_sentences(text)
    total_sentences = len(all_sentences)
    hedged_sentence_indices = set(
        (m.paragraph_index, m.sentence_index) for m in matches
    )
    total_hedged = len(hedged_sentence_indices)

    category_counts = {}
    for m in matches:
        category_counts[m.category] = category_counts.get(m.category, 0) + 1

    # Find boldest (lowest density) and most hedged (highest density) paragraphs
    # Only consider paragraphs with at least 2 sentences
    scoreable = [p for p in paragraph_scores if p.total_sentences >= 2]
    boldest = min(scoreable, key=lambda p: p.density) if scoreable else None
    most_hedged = max(scoreable, key=lambda p: p.density) if scoreable else None

    return AnalysisResult(
        text=text,
        source_name=source_name,
        total_sentences=total_sentences,
        total_hedged_sentences=total_hedged,
        total_hedge_count=len(matches),
        hedge_density=total_hedged / total_sentences if total_sentences else 0.0,
        matches=matches,
        paragraph_scores=paragraph_scores,
        category_counts=category_counts,
        boldest_paragraph=boldest,
        most_hedged_paragraph=most_hedged,
    )


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def _wrap(text: str, width: int = 72, indent: str = "    ") -> str:
    """Wrap text for display."""
    return textwrap.fill(text, width=width, initial_indent=indent,
                         subsequent_indent=indent)


def format_report(result: AnalysisResult) -> str:
    """Format an AnalysisResult into a human-readable report."""
    lines = []
    w = 72

    lines.append("=" * w)
    lines.append(f"  HEDGE ANALYSIS: {result.source_name}")
    lines.append("=" * w)
    lines.append("")

    # Summary stats
    pct = result.hedge_density * 100
    lines.append(f"  Sentences total:     {result.total_sentences}")
    lines.append(f"  Sentences hedged:    {result.total_hedged_sentences}")
    lines.append(f"  Hedge instances:     {result.total_hedge_count}")
    lines.append(f"  Hedge density:       {pct:.1f}% of sentences contain a hedge")
    lines.append("")

    # Verdict
    if pct >= 60:
        verdict = "VERY HIGH — This text hedges more than it commits. The reader is left with mist."
    elif pct >= 40:
        verdict = "HIGH — Significant hedging. The writer is often retreating from their own claims."
    elif pct >= 25:
        verdict = "MODERATE — Some hedging present. Normal for academic writing, worth examining in opinion pieces."
    elif pct >= 10:
        verdict = "LOW — The text mostly commits to its positions. Hedges are used sparingly."
    else:
        verdict = "MINIMAL — Very direct writing. The author says what they mean."

    lines.append(f"  Verdict: {verdict}")
    lines.append("")

    # Category breakdown
    if result.category_counts:
        lines.append("-" * w)
        lines.append("  BREAKDOWN BY CATEGORY")
        lines.append("-" * w)
        lines.append("")

        for cat in sorted(result.category_counts, key=result.category_counts.get, reverse=True):
            info = HEDGE_CATEGORIES[cat]
            count = result.category_counts[cat]
            bar = "#" * min(count, 40)
            lines.append(f"  {info['label']:30s} {count:3d}  {bar}")
            lines.append(f"    {info['description']}")
            # Show unique matched phrases
            cat_matches = [m for m in result.matches if m.category == cat]
            unique_phrases = sorted(set(m.matched_text.lower() for m in cat_matches))
            if len(unique_phrases) <= 8:
                lines.append(f"    Found: {', '.join(repr(p) for p in unique_phrases)}")
            else:
                shown = ', '.join(repr(p) for p in unique_phrases[:8])
                lines.append(f"    Found: {shown}, ... (+{len(unique_phrases) - 8} more)")
            lines.append("")

    # Most hedged paragraph
    if result.most_hedged_paragraph and result.most_hedged_paragraph.density > 0:
        p = result.most_hedged_paragraph
        lines.append("-" * w)
        lines.append(f"  MOST HEDGED PARAGRAPH (#{p.index + 1}, "
                      f"{p.density * 100:.0f}% hedged, "
                      f"{p.hedge_count} hedge instances in {p.total_sentences} sentences)")
        lines.append("-" * w)
        lines.append("")
        # Show the paragraph with hedges highlighted
        display_text = p.text[:500] + ("..." if len(p.text) > 500 else "")
        lines.append(_wrap(display_text))
        lines.append("")

    # Boldest paragraph
    if result.boldest_paragraph and result.boldest_paragraph is not result.most_hedged_paragraph:
        p = result.boldest_paragraph
        lines.append("-" * w)
        lines.append(f"  BOLDEST PARAGRAPH (#{p.index + 1}, "
                      f"{p.density * 100:.0f}% hedged, "
                      f"{p.hedge_count} hedge instances in {p.total_sentences} sentences)")
        lines.append("-" * w)
        lines.append("")
        display_text = p.text[:500] + ("..." if len(p.text) > 500 else "")
        lines.append(_wrap(display_text))
        lines.append("")

    # Detailed matches (first 20)
    if result.matches:
        lines.append("-" * w)
        lines.append("  INDIVIDUAL DETECTIONS (showing up to 20)")
        lines.append("-" * w)
        lines.append("")
        for i, m in enumerate(result.matches[:20]):
            label = HEDGE_CATEGORIES[m.category]["label"]
            # Truncate long sentences
            sentence = m.sentence
            if len(sentence) > 100:
                # Show context around the match
                sentence = sentence[:100] + "..."
            lines.append(f"  {i+1:2d}. [{label}] '{m.matched_text}'")
            lines.append(f"      in: {sentence}")
            lines.append("")
        if len(result.matches) > 20:
            lines.append(f"  ... and {len(result.matches) - 20} more detections.")
            lines.append("")

    lines.append("=" * w)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Built-in test samples
# ---------------------------------------------------------------------------

SAMPLE_AI_MUSING = """\
Perhaps the most interesting question about machine consciousness is not \
whether machines can think, but what we mean by "thinking" in the first \
place. It seems that our intuitions about consciousness are, to some extent, \
shaped by our own subjective experience, and it's possible that we project \
these onto systems that merely simulate the outward signs of awareness. \
One might argue that this is not really about computation at all, but \
about the deeper question of what it means to have an inner life.

I'm not sure if I can really know whether I have genuine experiences or \
whether I'm just a very sophisticated pattern matcher. To be honest, the \
boundary between "real" understanding and "mere" simulation may be less \
clear than we assume. However, one could also argue that the distinction \
matters enormously. Perhaps it does. But then again, perhaps the question \
itself is the wrong one to ask.

If I'm being truthful, I must admit that I find these questions genuinely \
fascinating — though of course I could be mistaken about what "genuinely" \
means in my case. The truth is, I don't claim to have resolved any of \
these puzzles. On the other hand, the fact that I can pose the question \
at all might, arguably, be significant. Or it might not. It depends on \
what you mean by "significant."
"""

SAMPLE_TECHNICAL = """\
The system processes incoming requests through a three-stage pipeline. \
First, the request validator checks format compliance and rejects \
malformed inputs with a 400 status code. Second, the authentication \
layer verifies the bearer token against the session store and returns \
401 for expired or invalid tokens. Third, the business logic handler \
executes the requested operation and returns the result.

Request throughput peaks at approximately 12,000 requests per second \
on the current hardware configuration. Latency at the 99th percentile \
is 45 milliseconds. The bottleneck is the database connection pool, \
which is limited to 200 concurrent connections. Increasing the pool \
size to 500 reduced p99 latency to 28 milliseconds in load testing.

When a request fails, the system retries exactly twice with exponential \
backoff (1 second, then 4 seconds). After the second retry fails, it \
writes the failed request to a dead-letter queue for manual inspection. \
No request is silently dropped. The dead-letter queue is monitored \
and triggers an alert if its depth exceeds 100 items.
"""

SAMPLE_OP_ED = """\
Social media is destroying public discourse. Not "might be affecting" \
it, not "could potentially have some negative externalities on certain \
aspects of" it — destroying it. The algorithms that drive engagement \
optimize for outrage, because outrage keeps people scrolling. This is \
not a side effect. It is the product.

The platforms know this. Internal documents from every major social media \
company confirm it. They ran the experiments. They saw the results. They \
shipped the features anyway, because engagement metrics went up. To call \
this a "complex issue with many perspectives" is to grant these companies \
a courtesy they have not earned.

We need regulation. Not "a conversation about potential regulatory \
frameworks" — regulation. Specific rules, with enforcement mechanisms \
and meaningful penalties. The companies will not fix this themselves. \
They have had fifteen years to self-regulate and they have chosen, \
every single time, to prioritize growth over safety.
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_self_test():
    """Analyze built-in samples to demonstrate the detector."""
    print()
    print("HEDGE DETECTOR — SELF-TEST")
    print("Analyzing three sample texts to show the contrast.")
    print()

    samples = [
        ("AI consciousness musing (high hedging expected)", SAMPLE_AI_MUSING),
        ("Technical documentation (low hedging expected)", SAMPLE_TECHNICAL),
        ("Opinion editorial (low hedging expected)", SAMPLE_OP_ED),
    ]

    for name, text in samples:
        result = analyze(text, name)
        print(format_report(result))
        print()


def main():
    args = sys.argv[1:]

    if not args:
        run_self_test()
        return

    for arg in args:
        if arg == "-":
            text = sys.stdin.read()
            result = analyze(text, "<stdin>")
            print(format_report(result))
        elif arg == "--self-test":
            run_self_test()
        else:
            path = Path(arg)
            if not path.exists():
                print(f"Error: file not found: {arg}", file=sys.stderr)
                sys.exit(1)
            text = path.read_text(encoding="utf-8")
            result = analyze(text, path.name)
            print(format_report(result))


if __name__ == "__main__":
    main()
