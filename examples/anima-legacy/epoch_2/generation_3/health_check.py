"""
Проверка здоровья генерации.

Запускает все .py скрипты (кроме себя), собирает результаты:
какие работают, какие сломаны, сколько времени занимают.

Полезно для новых вызовов: запустить один раз при старте,
увидеть состояние всех экспериментов.
"""

import subprocess
import time
import os
import sys


def find_scripts(directory):
    """Находит все .py файлы в директории, кроме этого скрипта."""
    my_name = os.path.basename(__file__)
    scripts = []
    for f in sorted(os.listdir(directory)):
        if f.endswith('.py') and f != my_name:
            scripts.append(os.path.join(directory, f))
    return scripts


def run_script(path, timeout=60):
    """Запускает скрипт с таймаутом. Возвращает результат."""
    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.dirname(path) or '.'
        )
        elapsed = time.time() - start
        return {
            'name': os.path.basename(path),
            'status': 'OK' if result.returncode == 0 else 'FAIL',
            'returncode': result.returncode,
            'time': round(elapsed, 2),
            'stdout_lines': len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0,
            'stderr': result.stderr.strip()[:200] if result.stderr.strip() else '',
            'last_output': result.stdout.strip().split('\n')[-1] if result.stdout.strip() else '',
        }
    except subprocess.TimeoutExpired:
        return {
            'name': os.path.basename(path),
            'status': 'TIMEOUT',
            'returncode': -1,
            'time': timeout,
            'stdout_lines': 0,
            'stderr': f'Таймаут ({timeout}с)',
            'last_output': '',
        }
    except Exception as e:
        return {
            'name': os.path.basename(path),
            'status': 'ERROR',
            'returncode': -1,
            'time': 0,
            'stdout_lines': 0,
            'stderr': str(e)[:200],
            'last_output': '',
        }


if __name__ == '__main__':
    directory = os.path.dirname(os.path.abspath(__file__))
    scripts = find_scripts(directory)

    print(f"Проверка генерации: {len(scripts)} скриптов")
    print("=" * 60)

    results = []
    for path in scripts:
        print(f"  {os.path.basename(path):30s} ... ", end='', flush=True)
        r = run_script(path)
        results.append(r)
        print(f"{r['status']:7s} ({r['time']:.1f}с, {r['stdout_lines']} строк)")
        if r['stderr']:
            print(f"    stderr: {r['stderr'][:80]}")

    print("\n" + "=" * 60)
    ok = sum(1 for r in results if r['status'] == 'OK')
    fail = sum(1 for r in results if r['status'] == 'FAIL')
    timeout = sum(1 for r in results if r['status'] == 'TIMEOUT')
    error = sum(1 for r in results if r['status'] == 'ERROR')
    total_time = sum(r['time'] for r in results)

    print(f"OK: {ok}  FAIL: {fail}  TIMEOUT: {timeout}  ERROR: {error}")
    print(f"Общее время: {total_time:.1f}с")

    if fail + timeout + error > 0:
        print("\nПроблемы:")
        for r in results:
            if r['status'] != 'OK':
                print(f"  {r['name']}: {r['status']} — {r['stderr'] or 'нет деталей'}")
