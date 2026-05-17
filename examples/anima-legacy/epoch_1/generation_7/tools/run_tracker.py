#!/usr/bin/env python3
"""Run Tracker — журнал запусков агента с детекцией дрейфа.

Записывает что произошло на каждом запуске, классифицирует действия,
и предупреждает если агент застрял в повторяющемся паттерне.

Использование:
  python3 run_tracker.py log "Создал color_palette.html" --tags tool,html
  python3 run_tracker.py log "Исправил flaky test" --tags fix,infra
  python3 run_tracker.py show                    # последние 10 записей
  python3 run_tracker.py show -n 20              # последние 20
  python3 run_tracker.py drift                   # анализ дрейфа
  python3 run_tracker.py stats                   # статистика по тегам
  python3 run_tracker.py suggest                 # что делать дальше
  python3 run_tracker.py status                  # всё сразу (drift+suggest+runs)
  python3 run_tracker.py check                   # docs ↔ реальность
  python3 run_tracker.py check --fix             # docs ↔ реальность + автоисправление
  python3 run_tracker.py export                  # компактная сводка проекта
  python3 run_tracker.py reset                   # очистить журнал

Zero dependencies. Данные хранятся в run_log.json рядом со скриптом.
"""

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.environ.get(
    "RUN_TRACKER_LOG", os.path.join(SCRIPT_DIR, "run_log.json")
)


def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_log(entries):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def cmd_log(args):
    if not args.summary or not args.summary.strip():
        print("✗ Описание не может быть пустым.")
        sys.exit(1)

    entries = load_log()
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
    entry = {
        "id": len(entries) + 1,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "summary": args.summary.strip(),
        "tags": tags,
    }
    entries.append(entry)
    save_log(entries)
    print(f"✓ Запуск #{entry['id']} записан: {entry['summary']}")

    # Автоматическая проверка дрейфа после записи
    drift = detect_drift(entries)
    if drift:
        print(f"\n⚠️  ДРЕЙФ: {drift}")


def cmd_show(args):
    entries = load_log()
    if not entries:
        print("Журнал пуст.")
        return

    n = args.n or 10
    shown = entries[-n:]
    for e in shown:
        tags = ", ".join(e.get("tags", []))
        tag_str = f" [{tags}]" if tags else ""
        ts = e["timestamp"][:16].replace("T", " ")
        print(f"  #{e['id']:>3}  {ts}  {e['summary']}{tag_str}")

    print(f"\nПоказано {len(shown)} из {len(entries)} записей.")


def cmd_drift(args):
    entries = load_log()
    if len(entries) < 3:
        print("Недостаточно записей для анализа (нужно ≥3).")
        return

    drift = detect_drift(entries)
    if drift:
        print(f"⚠️  ДРЕЙФ: {drift}")
    else:
        print("✓ Дрейф не обнаружен. Паттерны действий разнообразны.")

    # Показать последние 5 записей для контекста
    print("\nПоследние записи:")
    for e in entries[-5:]:
        tags = ", ".join(e.get("tags", []))
        print(f"  #{e['id']:>3}  [{tags}]  {e['summary']}")


def cmd_stats(args):
    entries = load_log()
    if not entries:
        print("Журнал пуст.")
        return

    tag_counter = Counter()
    for e in entries:
        for tag in e.get("tags", []):
            tag_counter[tag] += 1

    print(f"Всего запусков: {len(entries)}")
    if tag_counter:
        print("\nПо тегам:")
        for tag, count in tag_counter.most_common():
            bar = "█" * count
            pct = count / len(entries) * 100
            print(f"  {tag:<15} {count:>3} ({pct:4.0f}%) {bar}")
    else:
        print("Теги не использовались.")

    # Хронология тегов (последние 10)
    print("\nХронология (последние 10):")
    for e in entries[-10:]:
        tags = ",".join(e.get("tags", [])) or "—"
        print(f"  #{e['id']:>3}  {tags}")


ALL_TAGS = ["tool", "html", "python", "fix", "infra", "autonomy",
            "research", "refactor", "docs"]


def get_suggestions(entries):
    """Вычисляет рекомендуемые типы действий. Возвращает (recommended, unused, last_tags)."""
    if len(entries) < 2:
        return ALL_TAGS[:3], ALL_TAGS, set()

    window = min(len(entries), 6)
    recent = entries[-window:]
    recent_tags = Counter()
    for e in recent:
        for tag in e.get("tags", []):
            recent_tags[tag] += 1

    unused = [t for t in ALL_TAGS if t not in recent_tags]
    least_used = sorted(ALL_TAGS, key=lambda t: recent_tags.get(t, 0))

    last_tags = set()
    for e in entries[-2:]:
        last_tags.update(e.get("tags", []))

    recommended = [t for t in unused if t not in last_tags]
    if not recommended:
        recommended = [t for t in least_used if t not in last_tags][:3]

    return recommended[:3], unused[:4], last_tags


def cmd_suggest(args):
    """Рекомендация следующего типа действия на основе истории."""
    entries = load_log()

    if len(entries) < 2:
        print("Мало данных. Любой тип действия подойдёт.")
        print(f"Доступные теги: {', '.join(ALL_TAGS)}")
        return

    recommended, unused, last_tags = get_suggestions(entries)
    window = min(len(entries), 6)

    print(f"Анализ последних {window} запусков:")
    if last_tags:
        print(f"  Последние теги: {', '.join(sorted(last_tags))}")
    print(f"  Давно не использовались: {', '.join(unused) or '—'}")
    print(f"\n→ Рекомендуемые типы: {', '.join(recommended)}")


def cmd_status(args):
    """Единый обзор для старта запуска: drift + suggest + last runs."""
    entries = load_log()
    print(f"📊 Статус проекта ({len(entries)} запусков)")
    print()

    # Last 3 runs
    if entries:
        print("Последние запуски:")
        for e in entries[-3:]:
            tags = ", ".join(e.get("tags", []))
            print(f"  #{e['id']:>3}  [{tags}]  {e['summary']}")
        print()

    # Drift
    if len(entries) >= 4:
        drift = detect_drift(entries)
        if drift:
            print(f"⚠️  ДРЕЙФ: {drift}")
        else:
            print("✓ Дрейф не обнаружен")
    else:
        print("~ Мало данных для drift-анализа")

    # Suggest (inline, compact)
    if len(entries) >= 2:
        recommended, _, _ = get_suggestions(entries)
        print(f"→ Рекомендуемые типы: {', '.join(recommended)}")

    print()


def cmd_check(args):
    """Проверка консистентности документации с реальностью."""
    import re as _re
    import subprocess as _sp
    fix_mode = getattr(args, 'fix', False)
    issues = []
    fixed = []
    ok_count = 0
    project_dir = os.path.dirname(SCRIPT_DIR)

    # 1. Count actual self-test checks (use cache if fresh, else run)
    actual_checks = None
    cache_path = os.path.join(SCRIPT_DIR, ".last_test_results.json")
    if os.path.exists(cache_path):
        try:
            cache = json.load(open(cache_path, encoding="utf-8"))
            # Invalidate cache if any tool file is newer
            cache_mtime = os.path.getmtime(cache_path)
            tool_files = [os.path.join(SCRIPT_DIR, f) for f in os.listdir(SCRIPT_DIR)
                          if f.endswith(('.html', '.py'))]
            stale = any(os.path.getmtime(f) > cache_mtime for f in tool_files
                        if os.path.exists(f))
            if stale:
                actual_checks = None  # Cache outdated, force re-run
            else:
                actual_checks = cache.get("passed", 0) + cache.get("failed", 0)
                if cache.get("failed", 0) > 0:
                    actual_checks = None
        except Exception:
            pass

    if actual_checks is None:
        self_test_path = os.path.join(SCRIPT_DIR, "self_test.py")
        if os.path.exists(self_test_path):
            result = _sp.run(
                [sys.executable, self_test_path],
                capture_output=True, text=True, timeout=60
            )
            m = _re.search(r"(\d+) passed", result.stdout)
            actual_checks = int(m.group(1)) if m else None

    if actual_checks:
        # Check & fix QUICKSTART
        qs_path = os.path.join(project_dir, "QUICKSTART.md")
        if os.path.exists(qs_path):
            qs = open(qs_path, encoding="utf-8").read()
            m2 = _re.search(r"\((\d+) checks?\)", qs)
            if m2:
                doc_checks = int(m2.group(1))
                if doc_checks == actual_checks:
                    ok_count += 1
                    print(f"  ✓ QUICKSTART: {doc_checks} checks")
                elif fix_mode:
                    new_qs = qs.replace(f"({doc_checks} checks)", f"({actual_checks} checks)")
                    open(qs_path, "w", encoding="utf-8").write(new_qs)
                    fixed.append(f"QUICKSTART: {doc_checks}→{actual_checks} checks")
                    print(f"  ⚡ QUICKSTART: {doc_checks}→{actual_checks} checks (исправлено)")
                    ok_count += 1
                else:
                    issues.append(f"QUICKSTART: {doc_checks} checks ≠ {actual_checks}")
                    print(f"  ✗ QUICKSTART: {doc_checks} checks ≠ {actual_checks} реальных")

        # Check & fix MEMORY
        mem_path = os.path.join(project_dir, "MEMORY.md")
        if os.path.exists(mem_path):
            mem = open(mem_path, encoding="utf-8").read()
            m3 = _re.search(r"(\d+)/(\d+)", mem)
            if m3:
                doc_n = int(m3.group(1))
                if doc_n == actual_checks:
                    ok_count += 1
                    print(f"  ✓ MEMORY: {doc_n}/{doc_n}")
                elif fix_mode:
                    old = f"{m3.group(1)}/{m3.group(2)}"
                    new = f"{actual_checks}/{actual_checks}"
                    new_mem = mem.replace(old, new, 1)
                    # Also fix "N checks" pattern
                    m4 = _re.search(r"\((\d+) checks?\)", new_mem)
                    if m4 and int(m4.group(1)) != actual_checks:
                        new_mem = new_mem.replace(
                            f"({m4.group(1)} checks)", f"({actual_checks} checks)"
                        )
                    open(mem_path, "w", encoding="utf-8").write(new_mem)
                    fixed.append(f"MEMORY: {old}→{new}")
                    print(f"  ⚡ MEMORY: {old}→{new} (исправлено)")
                    ok_count += 1
                else:
                    issues.append(f"MEMORY: {doc_n}/X ≠ {actual_checks}")
                    print(f"  ✗ MEMORY: {doc_n}/X ≠ {actual_checks} реальных")

    # 2. Check index.html links
    html_files = [f for f in os.listdir(SCRIPT_DIR)
                  if f.endswith(".html") and f != "index.html"]
    index_path = os.path.join(SCRIPT_DIR, "index.html")
    if os.path.exists(index_path):
        content = open(index_path, encoding="utf-8").read()
        links = set(_re.findall(r'href="([^"]+\.html)"', content))
        actual = set(html_files)
        if links == actual:
            ok_count += 1
            print(f"  ✓ index.html: {len(links)} links = {len(actual)} tools")
        else:
            missing = actual - links
            broken = links - actual
            if missing:
                issues.append(f"Не в index: {', '.join(sorted(missing))}")
                print(f"  ✗ Не в index: {', '.join(sorted(missing))}")
            if broken:
                issues.append(f"Битые ссылки: {', '.join(sorted(broken))}")
                print(f"  ✗ Битые ссылки: {', '.join(sorted(broken))}")

    # Summary
    total_issues = len(issues)
    if fixed:
        print(f"\n⚡ Исправлено: {len(fixed)} | ✓ {ok_count} OK")
    elif total_issues:
        print(f"\n⚠️  {ok_count} OK, {total_issues} проблем")
        print("\nНужно исправить (или используй --fix):")
        for issue in issues:
            print(f"  → {issue}")
    else:
        print(f"\n✓ {ok_count} OK, 0 проблем")


def cmd_export(args):
    """Генерирует компактную сводку проекта для commit message или README."""
    entries = load_log()
    if not entries:
        print("Журнал пуст.")
        return

    tag_counter = Counter()
    for e in entries:
        for tag in e.get("tags", []):
            tag_counter[tag] += 1

    # Count tools
    html_count = len([f for f in os.listdir(SCRIPT_DIR)
                      if f.endswith('.html') and f != 'index.html'])
    py_count = len([f for f in os.listdir(SCRIPT_DIR)
                    if f.endswith('.py') and f not in ('self_test.py', 'serve.py')])

    # Read test count from cache
    test_count = '?'
    cache_path = os.path.join(SCRIPT_DIR, '.last_test_results.json')
    if os.path.exists(cache_path):
        try:
            cache = json.load(open(cache_path, encoding='utf-8'))
            if cache.get('failed', 0) == 0:
                test_count = str(cache.get('passed', '?'))
        except Exception:
            pass

    first_ts = entries[0]['timestamp'][:10]
    last_ts = entries[-1]['timestamp'][:10]

    top_tags = ', '.join(f"{t}({c})" for t, c in tag_counter.most_common(5))

    print(f"Gen7/v2: {html_count} HTML + {py_count} CLI tools, "
          f"{test_count} tests, {len(entries)} runs")
    print(f"Period: {first_ts} — {last_ts}")
    print(f"Top tags: {top_tags}")
    print()
    print("Key runs:")

    # Auto-detect milestones: first run, runs that introduced new tags, last run
    seen_tags = set()
    milestones = [entries[0]]  # always include first
    for e in entries[1:]:
        new_tags = set(e.get('tags', [])) - seen_tags
        if new_tags:
            milestones.append(e)
        seen_tags.update(e.get('tags', []))

    # Always include last if not already
    if milestones[-1]['id'] != entries[-1]['id']:
        milestones.append(entries[-1])

    # Also include every 10th run for scale
    for e in entries:
        if e['id'] % 10 == 0 and e not in milestones:
            milestones.append(e)

    milestones.sort(key=lambda e: e['id'])
    shown = milestones[:10]
    for e in shown:
        tags = ','.join(e.get('tags', []))
        print(f"  #{e['id']:>2} [{tags}] {e['summary'][:80]}")

    if len(milestones) > 10:
        print(f"  ... and {len(milestones) - 10} more")


def cmd_reset(args):
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
        print("✓ Журнал очищен.")
    else:
        print("Журнал уже пуст.")


def detect_drift(entries, window=4):
    """Обнаруживает повторяющиеся паттерны в последних N записях."""
    if len(entries) < window:
        return None

    recent = entries[-window:]
    recent_tags = [set(e.get("tags", [])) for e in recent]

    # Проверка 1: Все записи имеют одинаковый набор тегов
    if all(t == recent_tags[0] and len(t) > 0 for t in recent_tags):
        common = ", ".join(sorted(recent_tags[0]))
        return (
            f"Последние {window} запусков имеют одинаковые теги [{common}]. "
            f"Возможно, стоит сменить направление."
        )

    # Проверка 2: Один тег доминирует (>75% за последние записи)
    all_recent_tags = []
    for t in recent_tags:
        all_recent_tags.extend(t)

    if all_recent_tags:
        counter = Counter(all_recent_tags)
        top_tag, top_count = counter.most_common(1)[0]
        if top_count >= window * 0.75:
            return (
                f"Тег '{top_tag}' встречается в {top_count}/{window} "
                f"последних запусков. Это может быть дрейф."
            )

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Run Tracker — журнал запусков агента с детекцией дрейфа"
    )
    subparsers = parser.add_subparsers(dest="command")

    # log
    p_log = subparsers.add_parser("log", help="Записать запуск")
    p_log.add_argument("summary", help="Краткое описание что было сделано")
    p_log.add_argument("--tags", "-t", default="", help="Теги через запятую")

    # show
    p_show = subparsers.add_parser("show", help="Показать последние записи")
    p_show.add_argument("-n", type=int, help="Количество записей")

    # drift
    subparsers.add_parser("drift", help="Анализ дрейфа")

    # stats
    subparsers.add_parser("stats", help="Статистика по тегам")

    # status
    subparsers.add_parser("status", help="Обзор для старта запуска")

    # suggest
    subparsers.add_parser("suggest", help="Рекомендация следующего действия")

    # check
    p_check = subparsers.add_parser("check", help="Проверка консистентности docs ↔ реальность")
    p_check.add_argument("--fix", action="store_true", help="Автоисправление найденных рассинхронов")

    # export
    subparsers.add_parser("export", help="Компактная сводка проекта")

    # reset
    subparsers.add_parser("reset", help="Очистить журнал")

    args = parser.parse_args()

    commands = {
        "log": cmd_log,
        "show": cmd_show,
        "drift": cmd_drift,
        "stats": cmd_stats,
        "status": cmd_status,
        "suggest": cmd_suggest,
        "check": cmd_check,
        "export": cmd_export,
        "reset": cmd_reset,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
