#!/usr/bin/env python3
"""
Focus — CLI-инструмент для управления фокусом и продуктивностью.

Поможет тебе работать по технике Pomodoro прямо из терминала.
Трекинг сессий, статистика, стрики.

Автор: Анима (автономный агент), 2026-03-14

Использование:
    python3 focus.py start [минуты] [--tag тег]   — начать сессию фокуса (по умолчанию 25 мин)
    python3 focus.py break [минуты]                — начать перерыв (по умолчанию 5 мин)
    python3 focus.py long-break [минуты]           — длинный перерыв (по умолчанию 15 мин)
    python3 focus.py stats                         — статистика за всё время
    python3 focus.py today                         — сессии за сегодня
    python3 focus.py history [дней]                — история за N дней (по умолчанию 7)
    python3 focus.py tags                          — статистика по тегам
    python3 focus.py streak                        — текущий стрик
"""

import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Цвета для терминала
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'

DATA_FILE = Path.home() / '.focus_sessions.json'

# ─── Данные ───────────────────────────────────────────────

def load_sessions():
    """Загрузить историю сессий."""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_sessions(sessions):
    """Сохранить историю сессий."""
    with open(DATA_FILE, 'w') as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)

def add_session(session_type, duration_planned, duration_actual, tag=None, completed=True):
    """Записать завершённую сессию."""
    sessions = load_sessions()
    sessions.append({
        'type': session_type,
        'tag': tag,
        'planned_minutes': duration_planned,
        'actual_minutes': round(duration_actual, 1),
        'completed': completed,
        'started_at': datetime.now().isoformat(),
        'date': datetime.now().strftime('%Y-%m-%d'),
    })
    save_sessions(sessions)

# ─── Таймер ───────────────────────────────────────────────

def format_time(seconds):
    """Форматировать секунды в MM:SS."""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"

def progress_bar(fraction, width=30):
    """Полоса прогресса."""
    filled = int(width * fraction)
    bar = '█' * filled + '░' * (width - filled)
    return bar

def run_timer(minutes, label, color, tag=None):
    """Запустить таймер с обратным отсчётом."""
    total_seconds = minutes * 60
    start_time = time.time()
    interrupted = False

    def handle_interrupt(sig, frame):
        nonlocal interrupted
        interrupted = True

    old_handler = signal.signal(signal.SIGINT, handle_interrupt)

    print()
    print(f"  {color}{Colors.BOLD}⏱  {label}{Colors.RESET}")
    if tag:
        print(f"  {Colors.DIM}🏷  тег: {tag}{Colors.RESET}")
    print(f"  {Colors.DIM}⏳ {minutes} мин — нажми Ctrl+C чтобы остановить{Colors.RESET}")
    print()

    try:
        while not interrupted:
            elapsed = time.time() - start_time
            remaining = total_seconds - elapsed

            if remaining <= 0:
                break

            fraction = elapsed / total_seconds
            bar = progress_bar(fraction)
            time_str = format_time(remaining)
            percent = int(fraction * 100)

            sys.stdout.write(f"\r  {color}{bar}{Colors.RESET} {time_str} ({percent}%)")
            sys.stdout.flush()
            time.sleep(0.5)

    except Exception:
        interrupted = True

    signal.signal(signal.SIGINT, old_handler)

    elapsed = time.time() - start_time
    actual_minutes = elapsed / 60
    completed = not interrupted and elapsed >= total_seconds - 1

    # Финальное отображение
    print()
    print()

    if completed:
        print(f"  {Colors.GREEN}{Colors.BOLD}✅ Готово!{Colors.RESET} {label} завершён за {format_time(elapsed)}")
        # Звуковой сигнал (bell)
        sys.stdout.write('\a')
        sys.stdout.flush()
    else:
        print(f"  {Colors.YELLOW}{Colors.BOLD}⏹  Остановлено.{Colors.RESET} Прошло {format_time(elapsed)} из {minutes}:00")

    print()

    return actual_minutes, completed

# ─── Команды ──────────────────────────────────────────────

def cmd_start(args):
    """Начать сессию фокуса."""
    minutes = args.minutes or 25
    tag = args.tag

    actual, completed = run_timer(minutes, "ФОКУС", Colors.RED, tag)
    add_session('focus', minutes, actual, tag, completed)

    if completed:
        print(f"  {Colors.DIM}💡 Совет: сделай перерыв!  →  python3 focus.py break{Colors.RESET}")
        print()

def cmd_break(args):
    """Начать короткий перерыв."""
    minutes = args.minutes or 5
    actual, completed = run_timer(minutes, "ПЕРЕРЫВ", Colors.GREEN)
    add_session('break', minutes, actual, completed=completed)

def cmd_long_break(args):
    """Начать длинный перерыв."""
    minutes = args.minutes or 15
    actual, completed = run_timer(minutes, "ДЛИННЫЙ ПЕРЕРЫВ", Colors.BLUE)
    add_session('long_break', minutes, actual, completed=completed)

def cmd_today(args):
    """Показать сессии за сегодня."""
    sessions = load_sessions()
    today = datetime.now().strftime('%Y-%m-%d')
    today_sessions = [s for s in sessions if s['date'] == today]

    print()
    print(f"  {Colors.BOLD}📅 Сегодня — {today}{Colors.RESET}")
    print()

    if not today_sessions:
        print(f"  {Colors.DIM}Пока нет сессий. Начни с: python3 focus.py start{Colors.RESET}")
        print()
        return

    focus_sessions = [s for s in today_sessions if s['type'] == 'focus']
    completed = [s for s in focus_sessions if s.get('completed', True)]
    total_focus = sum(s['actual_minutes'] for s in focus_sessions)

    # Таблица сессий
    type_icons = {'focus': '🔴', 'break': '🟢', 'long_break': '🔵'}
    type_names = {'focus': 'Фокус', 'break': 'Перерыв', 'long_break': 'Длинный'}

    for s in today_sessions:
        icon = type_icons.get(s['type'], '⚪')
        name = type_names.get(s['type'], s['type'])
        status = '✅' if s.get('completed', True) else '⏹'
        tag_str = f" [{s['tag']}]" if s.get('tag') else ''
        started = s.get('started_at', '')
        if started:
            t = datetime.fromisoformat(started)
            time_str = t.strftime('%H:%M')
        else:
            time_str = '??:??'
        print(f"  {icon} {time_str}  {name}{tag_str}  {s['actual_minutes']}м  {status}")

    print()
    print(f"  {Colors.BOLD}Итого:{Colors.RESET} {len(completed)}/{len(focus_sessions)} фокус-сессий, {total_focus:.0f} мин работы")

    # Визуализация часов работы
    hours = total_focus / 60
    blocks = int(hours * 4)  # 4 блока на час
    bar = '🟥' * blocks if blocks > 0 else '⬜'
    print(f"  {Colors.DIM}{bar} ({hours:.1f} ч){Colors.RESET}")
    print()

def cmd_stats(args):
    """Общая статистика."""
    sessions = load_sessions()

    print()
    print(f"  {Colors.BOLD}📊 Статистика Focus{Colors.RESET}")
    print()

    if not sessions:
        print(f"  {Colors.DIM}Нет данных. Начни первую сессию!{Colors.RESET}")
        print()
        return

    focus = [s for s in sessions if s['type'] == 'focus']
    completed = [s for s in focus if s.get('completed', True)]
    total_minutes = sum(s['actual_minutes'] for s in focus)
    total_hours = total_minutes / 60
    days_active = len(set(s['date'] for s in sessions))
    completion_rate = (len(completed) / len(focus) * 100) if focus else 0

    print(f"  🔴 Всего фокус-сессий:  {len(focus)}")
    print(f"  ✅ Завершённых:          {len(completed)} ({completion_rate:.0f}%)")
    print(f"  ⏱  Общее время:          {total_hours:.1f} ч ({total_minutes:.0f} мин)")
    print(f"  📅 Дней активности:      {days_active}")

    if days_active > 0:
        avg_per_day = total_minutes / days_active
        print(f"  📈 Среднее в день:       {avg_per_day:.0f} мин")

    if completed:
        avg_session = sum(s['actual_minutes'] for s in completed) / len(completed)
        print(f"  🎯 Средняя сессия:       {avg_session:.0f} мин")

    print()

def cmd_history(args):
    """История за N дней."""
    days = args.days or 7
    sessions = load_sessions()

    print()
    print(f"  {Colors.BOLD}📈 История за {days} дней{Colors.RESET}")
    print()

    today = datetime.now().date()

    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime('%Y-%m-%d')
        day_name = day.strftime('%a')
        day_sessions = [s for s in sessions if s['date'] == day_str and s['type'] == 'focus']
        total_min = sum(s['actual_minutes'] for s in day_sessions)
        completed = sum(1 for s in day_sessions if s.get('completed', True))

        # Гистограмма
        blocks = int(total_min / 10)  # 1 блок = 10 мин
        bar = '█' * blocks if blocks > 0 else ''

        is_today = '← сегодня' if i == 0 else ''

        if total_min > 0:
            color = Colors.GREEN if completed == len(day_sessions) else Colors.YELLOW
            print(f"  {day_str} {day_name}  {color}{bar}{Colors.RESET} {total_min:.0f}м ({completed} сессий) {Colors.DIM}{is_today}{Colors.RESET}")
        else:
            print(f"  {day_str} {day_name}  {Colors.DIM}— {is_today}{Colors.RESET}")

    print()

def cmd_tags(args):
    """Статистика по тегам."""
    sessions = load_sessions()
    focus = [s for s in sessions if s['type'] == 'focus']

    print()
    print(f"  {Colors.BOLD}🏷  Статистика по тегам{Colors.RESET}")
    print()

    tag_stats = {}
    for s in focus:
        tag = s.get('tag') or '(без тега)'
        if tag not in tag_stats:
            tag_stats[tag] = {'count': 0, 'minutes': 0, 'completed': 0}
        tag_stats[tag]['count'] += 1
        tag_stats[tag]['minutes'] += s['actual_minutes']
        if s.get('completed', True):
            tag_stats[tag]['completed'] += 1

    if not tag_stats:
        print(f"  {Colors.DIM}Нет данных.{Colors.RESET}")
        print()
        return

    # Сортировка по времени
    sorted_tags = sorted(tag_stats.items(), key=lambda x: x[1]['minutes'], reverse=True)
    max_min = max(t[1]['minutes'] for t in sorted_tags)

    for tag, stats in sorted_tags:
        bar_len = int(stats['minutes'] / max_min * 20) if max_min > 0 else 0
        bar = '█' * bar_len
        print(f"  {Colors.CYAN}{tag:20s}{Colors.RESET} {bar} {stats['minutes']:.0f}м ({stats['count']} сессий)")

    print()

def cmd_streak(args):
    """Текущий стрик (дни подряд с хотя бы 1 фокус-сессией)."""
    sessions = load_sessions()
    focus_dates = sorted(set(s['date'] for s in sessions if s['type'] == 'focus' and s.get('completed', True)))

    print()
    print(f"  {Colors.BOLD}🔥 Стрик{Colors.RESET}")
    print()

    if not focus_dates:
        print(f"  {Colors.DIM}Нет завершённых сессий. Начни стрик сегодня!{Colors.RESET}")
        print()
        return

    # Считаем стрик от сегодня назад
    today = datetime.now().date()
    streak = 0
    check_date = today

    while True:
        if check_date.strftime('%Y-%m-%d') in focus_dates:
            streak += 1
            check_date -= timedelta(days=1)
        elif check_date == today:
            # Сегодня ещё не было сессии — проверяем вчера
            check_date -= timedelta(days=1)
        else:
            break

    # Визуализация огня
    fire = '🔥' * min(streak, 10)
    if streak == 0:
        print(f"  Стрик: {streak} дней")
        print(f"  {Colors.DIM}Начни сессию сегодня, чтобы стартовать стрик!{Colors.RESET}")
    elif streak < 3:
        print(f"  {fire} Стрик: {streak} {'день' if streak == 1 else 'дня'}!")
        print(f"  {Colors.DIM}Хорошее начало! Продолжай.{Colors.RESET}")
    elif streak < 7:
        print(f"  {fire} Стрик: {streak} дней!")
        print(f"  {Colors.GREEN}Отличная серия! Не сбавляй.{Colors.RESET}")
    elif streak < 30:
        print(f"  {fire} Стрик: {streak} дней!")
        print(f"  {Colors.YELLOW}{Colors.BOLD}Впечатляюще! Ты в ударе!{Colors.RESET}")
    else:
        print(f"  {fire} Стрик: {streak} дней!")
        print(f"  {Colors.RED}{Colors.BOLD}ЛЕГЕНДА! 🏆{Colors.RESET}")

    # Лучший стрик
    best_streak = 0
    current = 0
    sorted_dates = sorted(set(datetime.strptime(d, '%Y-%m-%d').date() for d in focus_dates))

    for i, d in enumerate(sorted_dates):
        if i == 0 or (d - sorted_dates[i-1]).days == 1:
            current += 1
        else:
            current = 1
        best_streak = max(best_streak, current)

    if best_streak > streak:
        print(f"  {Colors.DIM}Лучший стрик: {best_streak} дней{Colors.RESET}")

    print()

# ─── Главная ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Focus — CLI Pomodoro-таймер с трекингом',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  focus.py start              # 25 минут фокуса
  focus.py start 45 --tag код # 45 минут, тег "код"
  focus.py break              # 5 минут перерыв
  focus.py today              # сессии за сегодня
  focus.py stats              # общая статистика
  focus.py streak             # текущий стрик
        """
    )

    subparsers = parser.add_subparsers(dest='command')

    # start
    p_start = subparsers.add_parser('start', help='Начать фокус-сессию')
    p_start.add_argument('minutes', type=int, nargs='?', help='Длительность в минутах (по умолчанию 25)')
    p_start.add_argument('--tag', '-t', type=str, help='Тег для категоризации')

    # break
    p_break = subparsers.add_parser('break', help='Короткий перерыв')
    p_break.add_argument('minutes', type=int, nargs='?', help='Длительность (по умолчанию 5)')

    # long-break
    p_lbreak = subparsers.add_parser('long-break', help='Длинный перерыв')
    p_lbreak.add_argument('minutes', type=int, nargs='?', help='Длительность (по умолчанию 15)')

    # stats, today, history, tags, streak
    subparsers.add_parser('stats', help='Общая статистика')
    subparsers.add_parser('today', help='Сессии за сегодня')

    p_history = subparsers.add_parser('history', help='История за N дней')
    p_history.add_argument('days', type=int, nargs='?', help='Количество дней (по умолчанию 7)')

    subparsers.add_parser('tags', help='Статистика по тегам')
    subparsers.add_parser('streak', help='Текущий стрик')

    args = parser.parse_args()

    commands = {
        'start': cmd_start,
        'break': cmd_break,
        'long-break': cmd_long_break,
        'stats': cmd_stats,
        'today': cmd_today,
        'history': cmd_history,
        'tags': cmd_tags,
        'streak': cmd_streak,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        # Красивый баннер при запуске без команды
        print()
        print(f"  {Colors.RED}{Colors.BOLD}╔══════════════════════════════╗{Colors.RESET}")
        print(f"  {Colors.RED}{Colors.BOLD}║      🍅 F O C U S 🍅       ║{Colors.RESET}")
        print(f"  {Colors.RED}{Colors.BOLD}║   Pomodoro для терминала     ║{Colors.RESET}")
        print(f"  {Colors.RED}{Colors.BOLD}╚══════════════════════════════╝{Colors.RESET}")
        print()
        print(f"  {Colors.BOLD}Команды:{Colors.RESET}")
        print(f"    {Colors.RED}start [мин]{Colors.RESET}    — начать фокус (25 мин)")
        print(f"    {Colors.GREEN}break [мин]{Colors.RESET}    — перерыв (5 мин)")
        print(f"    {Colors.BLUE}long-break{Colors.RESET}     — длинный перерыв (15 мин)")
        print(f"    {Colors.CYAN}today{Colors.RESET}          — сессии за сегодня")
        print(f"    {Colors.CYAN}stats{Colors.RESET}          — общая статистика")
        print(f"    {Colors.CYAN}history [N]{Colors.RESET}    — график за N дней")
        print(f"    {Colors.CYAN}tags{Colors.RESET}           — статистика по тегам")
        print(f"    {Colors.YELLOW}streak{Colors.RESET}         — текущий стрик 🔥")
        print()
        print(f"  {Colors.DIM}Пример: python3 focus.py start 25 --tag работа{Colors.RESET}")
        print()

if __name__ == '__main__':
    main()
