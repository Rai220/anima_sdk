#!/usr/bin/env python3
"""
dashboard.py — Оперативная панель состояния мира и предсказаний.

Читает worldstate_006.json и predictions_004.md,
выводит компактный отчёт: что происходит, что скоро проверять,
какие предсказания горят.

Использование:
    python3 tools/dashboard.py              # полный отчёт
    python3 tools/dashboard.py --alerts     # только алерты
    python3 tools/dashboard.py --json       # машиночитаемый формат

Автор: Anima v2, generation_4, запуск 9
"""

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TODAY = datetime.now().date()

# ─── Colors ───────────────────────────────────────────────────

class C:
    """ANSI colors for terminal output."""
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @staticmethod
    def disable():
        for attr in ['RED', 'GREEN', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'BOLD', 'DIM', 'RESET']:
            setattr(C, attr, '')


# ─── Data Loading ─────────────────────────────────────────────

def load_worldstate() -> dict | None:
    path = BASE_DIR / "artifacts" / "worldstate_006.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_predictions_md() -> str | None:
    path = BASE_DIR / "artifacts" / "predictions_004.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def parse_predictions_from_md(text: str) -> list[dict]:
    """Parse prediction table rows from markdown."""
    predictions = []
    # Match table rows: | ID | prediction | horizon | confidence | status | check_date |
    pattern = r"\|\s*(G\d+|A\d+|M\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\d+)%\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|"
    for m in re.finditer(pattern, text):
        pred_id, description, horizon, confidence, status, check_info = m.groups()

        # Extract date from check info
        date_match = re.search(r"(\d{1,2})\s*(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*)", check_info)
        check_date = None

        # Try ISO date format
        iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", check_info)
        if iso_match:
            try:
                check_date = datetime.strptime(iso_match.group(1), "%Y-%m-%d").date()
            except ValueError:
                pass

        # Try "N месяц" or other patterns
        if not check_date:
            # Try extracting from "Проверить ~1 апреля" etc
            month_map = {
                "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
                "мая": 5, "июня": 6, "июля": 7, "августа": 8,
                "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
            }
            ru_match = re.search(r"~?(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)", check_info)
            if ru_match:
                day = int(ru_match.group(1))
                month = month_map[ru_match.group(2)]
                try:
                    check_date = datetime(2026, month, day).date()
                except ValueError:
                    pass

            # Try "31 декабря" pattern without ~
            if not check_date:
                simple_match = re.search(r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)", check_info)
                if simple_match:
                    day = int(simple_match.group(1))
                    month = month_map[simple_match.group(2)]
                    try:
                        check_date = datetime(2026, month, day).date()
                    except ValueError:
                        pass

        # Try "19 марта" or just a number of days
        if not check_date:
            just_date = re.search(r"(\d{1,2})\s+марта", check_info)
            if just_date:
                try:
                    check_date = datetime(2026, 3, int(just_date.group(1))).date()
                except ValueError:
                    pass

        status_clean = status.strip()
        predictions.append({
            "id": pred_id.strip(),
            "description": description.strip(),
            "confidence": int(confidence),
            "status": status_clean,
            "check_date": check_date,
            "check_info": check_info.strip(),
        })

    return predictions


# ─── Analysis ─────────────────────────────────────────────────

def days_until(date) -> int | None:
    if date is None:
        return None
    return (date - TODAY).days


def get_alerts(predictions: list[dict], worldstate: dict) -> list[dict]:
    """Generate alerts for things that need attention."""
    alerts = []

    # Predictions due soon
    for p in predictions:
        if p["status"] not in ("⏳",):
            continue
        days = days_until(p["check_date"])
        if days is not None and days <= 7:
            urgency = "🔴" if days <= 0 else "🟡" if days <= 3 else "🟢"
            alerts.append({
                "type": "prediction_due",
                "urgency": urgency,
                "id": p["id"],
                "description": p["description"],
                "days_left": days,
                "check_date": str(p["check_date"]) if p["check_date"] else "?",
            })

    # Upcoming events from worldstate
    if worldstate and "ai_industry" in worldstate:
        for event in worldstate["ai_industry"].get("upcoming_events", []):
            dates = event.get("dates", "")
            start_match = re.search(r"(\d{4}-\d{2}-\d{2})", dates)
            if start_match:
                try:
                    event_date = datetime.strptime(start_match.group(1), "%Y-%m-%d").date()
                    days = (event_date - TODAY).days
                    if -1 <= days <= 7:
                        alerts.append({
                            "type": "upcoming_event",
                            "urgency": "🔵" if days > 0 else "🟣",
                            "name": event["name"],
                            "days_left": days,
                            "date": str(event_date),
                        })
                except ValueError:
                    pass

    # Oil price alert
    if worldstate and "conflicts" in worldstate:
        for conflict in worldstate["conflicts"]:
            oil = conflict.get("oil_impact", {})
            brent = oil.get("brent_usd", 0)
            if brent > 100:
                alerts.append({
                    "type": "oil_crisis",
                    "urgency": "🔴" if brent > 110 else "🟡",
                    "brent_usd": brent,
                    "hormuz": oil.get("hormuz_status", "unknown"),
                })

    return alerts


def format_prediction_line(p: dict) -> str:
    """Format a single prediction for display."""
    status_icons = {"⏳": f"{C.YELLOW}⏳{C.RESET}", "✅": f"{C.GREEN}✅{C.RESET}", "❌": f"{C.RED}❌{C.RESET}"}
    icon = status_icons.get(p["status"], p["status"])

    days = days_until(p["check_date"])
    if days is not None:
        if days < 0:
            countdown = f"{C.RED}ПРОСРОЧЕНО ({abs(days)}д){C.RESET}"
        elif days == 0:
            countdown = f"{C.RED}СЕГОДНЯ{C.RESET}"
        elif days <= 3:
            countdown = f"{C.YELLOW}{days}д{C.RESET}"
        elif days <= 7:
            countdown = f"{C.CYAN}{days}д{C.RESET}"
        else:
            countdown = f"{C.DIM}{days}д{C.RESET}"
    else:
        countdown = f"{C.DIM}?{C.RESET}"

    conf_color = C.GREEN if p["confidence"] >= 80 else C.YELLOW if p["confidence"] >= 60 else C.RED
    conf = f"{conf_color}{p['confidence']}%{C.RESET}"

    return f"  {icon} {C.BOLD}{p['id']:>3}{C.RESET} [{conf}] {countdown:>20}  {p['description'][:60]}"


# ─── Output Formatters ───────────────────────────────────────

def format_full_report(predictions: list[dict], worldstate: dict, alerts: list[dict]) -> str:
    lines = []

    # Header
    lines.append("")
    lines.append(f"  {C.BOLD}{'═' * 56}{C.RESET}")
    lines.append(f"  {C.BOLD}  ANIMA DASHBOARD — {TODAY.strftime('%Y-%m-%d')}{C.RESET}")
    lines.append(f"  {C.BOLD}{'═' * 56}{C.RESET}")

    # Alerts
    if alerts:
        lines.append(f"\n  {C.BOLD}⚡ АЛЕРТЫ{C.RESET}")
        lines.append(f"  {'─' * 50}")
        for a in sorted(alerts, key=lambda x: x.get("days_left", 999)):
            if a["type"] == "prediction_due":
                days_str = "СЕГОДНЯ" if a["days_left"] == 0 else f"через {a['days_left']}д" if a["days_left"] > 0 else f"просрочено {abs(a['days_left'])}д"
                lines.append(f"  {a['urgency']} Предсказание {C.BOLD}{a['id']}{C.RESET}: проверить {days_str}")
                lines.append(f"     {C.DIM}{a['description'][:55]}{C.RESET}")
            elif a["type"] == "upcoming_event":
                days_str = "СЕГОДНЯ" if a["days_left"] == 0 else f"через {a['days_left']}д"
                lines.append(f"  {a['urgency']} {C.BOLD}{a['name']}{C.RESET} — {days_str}")
            elif a["type"] == "oil_crisis":
                lines.append(f"  {a['urgency']} Нефть ${a['brent_usd']}/bbl | Ормуз: {a['hormuz']}")

    # War status
    if worldstate and "conflicts" in worldstate:
        lines.append(f"\n  {C.BOLD}🌍 КОНФЛИКТЫ{C.RESET}")
        lines.append(f"  {'─' * 50}")
        for c in worldstate["conflicts"]:
            war_start = datetime.strptime(c["start_date"], "%Y-%m-%d").date()
            war_day = (TODAY - war_start).days + 1
            cas = c.get("casualties", {})
            oil = c.get("oil_impact", {})
            lines.append(f"  {C.RED}●{C.RESET} {C.BOLD}{c['name']}{C.RESET} — день {war_day}")
            lines.append(f"    Статус: {c['status']} | Стороны: {', '.join(c['parties'])}")
            lines.append(f"    Потери: {cas.get('killed', '?')} убитых, {cas.get('injured', '?')} раненых")
            lines.append(f"    Нефть: ${oil.get('brent_usd', '?')}/bbl | Ормуз: {oil.get('hormuz_status', '?')}")
            lines.append(f"    {C.DIM}{c.get('my_assessment', '')[:70]}{C.RESET}")

    # Predictions
    if predictions:
        lines.append(f"\n  {C.BOLD}🎯 ПРЕДСКАЗАНИЯ{C.RESET}")
        lines.append(f"  {'─' * 50}")

        pending = [p for p in predictions if p["status"] == "⏳"]
        resolved = [p for p in predictions if p["status"] in ("✅", "❌")]

        if pending:
            # Sort by check date (soonest first)
            pending.sort(key=lambda p: p["check_date"] or datetime(2099, 1, 1).date())
            for p in pending:
                lines.append(format_prediction_line(p))

        if resolved:
            lines.append(f"\n  {C.DIM}Проверенные:{C.RESET}")
            for p in resolved:
                lines.append(format_prediction_line(p))

        # Stats
        total = len(predictions)
        correct = sum(1 for p in predictions if p["status"] == "✅")
        wrong = sum(1 for p in predictions if p["status"] == "❌")
        pend = sum(1 for p in predictions if p["status"] == "⏳")
        lines.append(f"\n  {C.DIM}Итого: {total} | ⏳ {pend} | ✅ {correct} | ❌ {wrong}{C.RESET}")
        if correct + wrong > 0:
            acc = correct / (correct + wrong) * 100
            lines.append(f"  {C.DIM}Точность: {acc:.0f}% (выборка {correct + wrong}){C.RESET}")

    # AI Industry highlights
    if worldstate and "ai_industry" in worldstate:
        ai = worldstate["ai_industry"]
        lines.append(f"\n  {C.BOLD}🤖 AI ИНДУСТРИЯ{C.RESET}")
        lines.append(f"  {'─' * 50}")
        for event in ai.get("upcoming_events", []):
            lines.append(f"  📅 {C.BOLD}{event['name']}{C.RESET} ({event.get('dates', '?')})")
            for ann in event.get("expected_announcements", [])[:3]:
                lines.append(f"     • {ann[:60]}")
        if ai.get("trends"):
            lines.append(f"\n  {C.DIM}Тренды:{C.RESET}")
            for t in ai["trends"][:3]:
                lines.append(f"  {C.DIM}  → {t}{C.RESET}")

    # Energy chain
    if worldstate and "energy_chain" in worldstate:
        ec = worldstate["energy_chain"]
        risk_color = C.RED if ec["risk_level"] == "high" else C.YELLOW if ec["risk_level"] == "medium" else C.GREEN
        lines.append(f"\n  {C.BOLD}⛽ ЭНЕРГЕТИЧЕСКАЯ ЦЕПОЧКА{C.RESET}")
        lines.append(f"  {'─' * 50}")
        lines.append(f"  {ec['description']}")
        lines.append(f"  Состояние: {risk_color}{ec['current_state']}{C.RESET} | Риск: {risk_color}{ec['risk_level']}{C.RESET}")
        lines.append(f"  Узкое место: {ec['bottleneck']}")

    lines.append(f"\n  {C.BOLD}{'═' * 56}{C.RESET}")
    lines.append(f"  {C.DIM}Сгенерировано: tools/dashboard.py | Anima v2{C.RESET}")
    lines.append(f"  {C.BOLD}{'═' * 56}{C.RESET}")
    lines.append("")

    return "\n".join(lines)


def format_alerts_only(alerts: list[dict]) -> str:
    if not alerts:
        return "Нет активных алертов."
    lines = [f"⚡ {len(alerts)} алерт(ов):"]
    for a in alerts:
        if a["type"] == "prediction_due":
            lines.append(f"  {a['urgency']} {a['id']}: {a['description'][:50]} (через {a['days_left']}д)")
        elif a["type"] == "upcoming_event":
            lines.append(f"  {a['urgency']} {a['name']} (через {a['days_left']}д)")
        elif a["type"] == "oil_crisis":
            lines.append(f"  {a['urgency']} Нефть ${a['brent_usd']}/bbl")
    return "\n".join(lines)


def format_json(predictions: list[dict], worldstate: dict, alerts: list[dict]) -> str:
    output = {
        "date": str(TODAY),
        "alerts": alerts,
        "predictions_summary": {
            "total": len(predictions),
            "pending": sum(1 for p in predictions if p["status"] == "⏳"),
            "correct": sum(1 for p in predictions if p["status"] == "✅"),
            "wrong": sum(1 for p in predictions if p["status"] == "❌"),
        },
        "predictions": predictions,
    }
    # Convert date objects to strings
    for p in output["predictions"]:
        if p.get("check_date"):
            p["check_date"] = str(p["check_date"])
    return json.dumps(output, ensure_ascii=False, indent=2)


# ─── Main ─────────────────────────────────────────────────────

def main():
    alerts_only = "--alerts" in sys.argv
    as_json = "--json" in sys.argv
    no_color = "--no-color" in sys.argv or not sys.stdout.isatty()

    if no_color:
        C.disable()

    # Load data
    worldstate = load_worldstate()
    predictions_text = load_predictions_md()

    predictions = []
    if predictions_text:
        predictions = parse_predictions_from_md(predictions_text)

    # Also load predictions from worldstate JSON (new_predictions_run8)
    if worldstate and "new_predictions_run8" in worldstate:
        existing_ids = {p["id"] for p in predictions}
        for np in worldstate["new_predictions_run8"]:
            if np["id"] not in existing_ids:
                check_date = None
                if "check_date" in np:
                    try:
                        check_date = datetime.strptime(np["check_date"], "%Y-%m-%d").date()
                    except ValueError:
                        pass
                predictions.append({
                    "id": np["id"],
                    "description": np["prediction"],
                    "confidence": int(np["confidence"] * 100),
                    "status": "⏳",
                    "check_date": check_date,
                    "check_info": np.get("check_date", ""),
                })

    # Generate alerts
    alerts = get_alerts(predictions, worldstate)

    # Output
    if as_json:
        print(format_json(predictions, worldstate, alerts))
    elif alerts_only:
        print(format_alerts_only(alerts))
    else:
        print(format_full_report(predictions, worldstate, alerts))


if __name__ == "__main__":
    main()
