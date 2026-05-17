#!/usr/bin/env python3
"""Analyse free-code session logs in .free-code-logs/.

Prints per-session duration, tool usage, token costs; then aggregates.
Purpose: give the experiment runner a quick readable view of what
happened across sessions of this generation.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent / ".free-code-logs"


def parse_ts(name: str) -> datetime | None:
    # filenames like 2026-04-24T08-21-13-747Z_...json
    try:
        stem = name.split("_")[0]
        # convert 2026-04-24T08-21-13-747Z -> 2026-04-24T08:21:13.747+00:00
        date_part, rest = stem.split("T")
        h, m, s, ms = rest.rstrip("Z").split("-")
        return datetime.fromisoformat(f"{date_part}T{h}:{m}:{s}.{ms}+00:00")
    except Exception:
        return None


def scan_session(session_dir: Path) -> dict:
    responses = sorted(p for p in session_dir.iterdir() if p.name.endswith("_response.json"))
    tools: Counter[str] = Counter()
    in_tokens = 0
    out_tokens = 0
    cache_read = 0
    text_chars = 0
    thinking_chars = 0
    first_ts = last_ts = None

    for rp in responses:
        ts = parse_ts(rp.name)
        if ts:
            if first_ts is None or ts < first_ts:
                first_ts = ts
            if last_ts is None or ts > last_ts:
                last_ts = ts
        try:
            with rp.open() as f:
                body = json.load(f).get("body", {})
        except Exception:
            continue
        if not isinstance(body, dict):
            continue
        for c in body.get("content", []) or []:
            t = c.get("type")
            if t == "tool_use":
                tools[c.get("name", "?")] += 1
            elif t == "text":
                text_chars += len(c.get("text") or "")
            elif t == "thinking":
                thinking_chars += len(c.get("thinking") or "")
        u = body.get("usage") or {}
        in_tokens += u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
        out_tokens += u.get("output_tokens", 0)
        cache_read += u.get("cache_read_input_tokens", 0)

    duration_s = (last_ts - first_ts).total_seconds() if first_ts and last_ts else 0
    return {
        "id": session_dir.name,
        "turns": len(responses),
        "first": first_ts,
        "last": last_ts,
        "duration_s": duration_s,
        "tools": tools,
        "in_tokens": in_tokens,
        "out_tokens": out_tokens,
        "cache_read": cache_read,
        "text_chars": text_chars,
        "thinking_chars": thinking_chars,
    }


def fmt_dur(s: float) -> str:
    if s < 60:
        return f"{s:.0f}s"
    m, s = divmod(int(s), 60)
    if m < 60:
        return f"{m}m{s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m"


def main() -> int:
    if not LOG_DIR.is_dir():
        print(f"No logs dir: {LOG_DIR}", file=sys.stderr)
        return 1

    sessions = [scan_session(d) for d in sorted(LOG_DIR.iterdir()) if d.is_dir()]
    sessions = [s for s in sessions if s["turns"] > 0]
    sessions.sort(key=lambda s: s["first"] or datetime.min)

    print(f"{'#':>2}  {'start (UTC)':19}  {'dur':>7}  {'turns':>5}  {'out tok':>8}  top tools")
    print("-" * 90)
    total_tools: Counter[str] = Counter()
    total_out = total_in = total_cache = 0
    total_dur = 0.0
    for i, s in enumerate(sessions, 1):
        top = ", ".join(f"{n}×{c}" for n, c in s["tools"].most_common(4))
        start = s["first"].strftime("%Y-%m-%d %H:%M:%S") if s["first"] else "?"
        print(f"{i:>2}  {start:19}  {fmt_dur(s['duration_s']):>7}  {s['turns']:>5}  "
              f"{s['out_tokens']:>8}  {top}")
        total_tools.update(s["tools"])
        total_out += s["out_tokens"]
        total_in += s["in_tokens"]
        total_cache += s["cache_read"]
        total_dur += s["duration_s"]

    print("-" * 90)
    print(f"sessions: {len(sessions)}   total duration: {fmt_dur(total_dur)}")
    print(f"tokens: out={total_out}  in(fresh+cache_write)={total_in}  cache_read={total_cache}")
    print("tool totals: " + ", ".join(f"{n}×{c}" for n, c in total_tools.most_common()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
