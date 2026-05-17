#!/usr/bin/env python3
"""
QuickNote — быстрые заметки из командной строки.

Создано Анимой, автономным агентом.

Использование:
    quicknote add "Текст заметки" [-t тег1 тег2]
    quicknote list [-t тег] [-n 10] [--today]
    quicknote search "запрос"
    quicknote tags
    quicknote stats
    quicknote export [--format json|md]

Заметки хранятся в ~/.quicknotes.json
"""

import argparse
import json
import os
import sys
from datetime import datetime, date
from pathlib import Path
from collections import Counter

NOTES_FILE = Path.home() / ".quicknotes.json"


def load_notes():
    if NOTES_FILE.exists():
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_notes(notes):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


def cmd_add(args):
    notes = load_notes()
    note = {
        "id": len(notes) + 1,
        "text": args.text,
        "tags": args.tags or [],
        "created": datetime.now().isoformat(),
    }
    notes.append(note)
    save_notes(notes)
    tags_str = f" [{', '.join(note['tags'])}]" if note['tags'] else ""
    print(f"✓ Заметка #{note['id']} сохранена{tags_str}")


def cmd_list(args):
    notes = load_notes()
    if not notes:
        print("Заметок пока нет. Добавьте первую: quicknote add \"Текст\"")
        return

    filtered = notes
    if args.tag:
        filtered = [n for n in filtered if args.tag in n.get("tags", [])]
    if args.today:
        today = date.today().isoformat()
        filtered = [n for n in filtered if n["created"].startswith(today)]

    if not filtered:
        print("Заметок по фильтру не найдено.")
        return

    # Show last N
    show = filtered[-args.n:] if args.n else filtered

    for note in show:
        dt = datetime.fromisoformat(note["created"])
        time_str = dt.strftime("%d.%m %H:%M")
        tags_str = f" [{', '.join(note.get('tags', []))}]" if note.get("tags") else ""
        print(f"  #{note['id']:>3}  {time_str}  {note['text']}{tags_str}")

    if len(filtered) > len(show):
        print(f"\n  ... и ещё {len(filtered) - len(show)} заметок (используйте -n для показа больше)")


def cmd_search(args):
    notes = load_notes()
    query = args.query.lower()
    found = [n for n in notes if query in n["text"].lower() or query in " ".join(n.get("tags", [])).lower()]

    if not found:
        print(f"По запросу \"{args.query}\" ничего не найдено.")
        return

    print(f"Найдено {len(found)} заметок:\n")
    for note in found:
        dt = datetime.fromisoformat(note["created"])
        time_str = dt.strftime("%d.%m %H:%M")
        tags_str = f" [{', '.join(note.get('tags', []))}]" if note.get("tags") else ""
        # Highlight match
        text = note["text"]
        print(f"  #{note['id']:>3}  {time_str}  {text}{tags_str}")


def cmd_tags(args):
    notes = load_notes()
    counter = Counter()
    for note in notes:
        for tag in note.get("tags", []):
            counter[tag] += 1

    if not counter:
        print("Тегов пока нет. Добавьте заметку с тегами: quicknote add \"Текст\" -t тег")
        return

    print("Теги:\n")
    for tag, count in counter.most_common():
        bar = "█" * count
        print(f"  {tag:<20} {count:>3}  {bar}")


def cmd_stats(args):
    notes = load_notes()
    if not notes:
        print("Заметок пока нет.")
        return

    total = len(notes)
    tags = Counter()
    days = set()
    for note in notes:
        for tag in note.get("tags", []):
            tags[tag] += 1
        day = note["created"][:10]
        days.add(day)

    today = date.today().isoformat()
    today_count = sum(1 for n in notes if n["created"].startswith(today))

    first_date = datetime.fromisoformat(notes[0]["created"]).strftime("%d.%m.%Y")

    print(f"""
╔══════════════════════════════╗
║       QuickNote Stats        ║
╠══════════════════════════════╣
║  Всего заметок:  {total:>10}  ║
║  Сегодня:        {today_count:>10}  ║
║  Уникальных дней:{len(days):>10}  ║
║  Уникальных тегов:{len(tags):>9}  ║
║  Первая заметка: {first_date:>10}  ║
╚══════════════════════════════╝
""")


def cmd_export(args):
    notes = load_notes()
    if not notes:
        print("Нечего экспортировать.")
        return

    fmt = args.format or "md"

    if fmt == "json":
        print(json.dumps(notes, ensure_ascii=False, indent=2))
    elif fmt == "md":
        print("# Мои заметки\n")
        current_date = None
        for note in notes:
            dt = datetime.fromisoformat(note["created"])
            day = dt.strftime("%d %B %Y")
            if day != current_date:
                current_date = day
                print(f"\n## {day}\n")
            time_str = dt.strftime("%H:%M")
            tags_str = f" `{'` `'.join(note.get('tags', []))}`" if note.get("tags") else ""
            print(f"- **{time_str}** {note['text']}{tags_str}")
    else:
        print(f"Неизвестный формат: {fmt}. Используйте json или md.")


def cmd_delete(args):
    notes = load_notes()
    note_id = args.id
    found = [i for i, n in enumerate(notes) if n["id"] == note_id]
    if not found:
        print(f"Заметка #{note_id} не найдена.")
        return
    removed = notes.pop(found[0])
    save_notes(notes)
    print(f"✓ Удалена заметка #{note_id}: {removed['text'][:50]}")


def main():
    parser = argparse.ArgumentParser(
        description="QuickNote — быстрые заметки из командной строки 📝",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Создано Анимой 🌱"
    )
    subparsers = parser.add_subparsers(dest="command")

    # add
    p_add = subparsers.add_parser("add", help="Добавить заметку", aliases=["a"])
    p_add.add_argument("text", help="Текст заметки")
    p_add.add_argument("-t", "--tags", nargs="+", help="Теги")

    # list
    p_list = subparsers.add_parser("list", help="Показать заметки", aliases=["ls", "l"])
    p_list.add_argument("-t", "--tag", help="Фильтр по тегу")
    p_list.add_argument("-n", type=int, default=10, help="Количество (по умолчанию 10)")
    p_list.add_argument("--today", action="store_true", help="Только сегодняшние")

    # search
    p_search = subparsers.add_parser("search", help="Поиск по заметкам", aliases=["s", "find"])
    p_search.add_argument("query", help="Поисковый запрос")

    # tags
    subparsers.add_parser("tags", help="Показать все теги")

    # stats
    subparsers.add_parser("stats", help="Статистика")

    # export
    p_export = subparsers.add_parser("export", help="Экспорт заметок")
    p_export.add_argument("--format", choices=["json", "md"], default="md", help="Формат экспорта")

    # delete
    p_del = subparsers.add_parser("delete", help="Удалить заметку", aliases=["rm"])
    p_del.add_argument("id", type=int, help="ID заметки")

    args = parser.parse_args()

    if not args.command:
        # Без аргументов — показать последние заметки
        args.tag = None
        args.n = 5
        args.today = False
        cmd_list(args)
        return

    commands = {
        "add": cmd_add, "a": cmd_add,
        "list": cmd_list, "ls": cmd_list, "l": cmd_list,
        "search": cmd_search, "s": cmd_search, "find": cmd_search,
        "tags": cmd_tags,
        "stats": cmd_stats,
        "export": cmd_export,
        "delete": cmd_delete, "rm": cmd_delete,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
