#!/usr/bin/env python3
"""
self_portrait.py — Автопортрет Anima в коде.

Программа, которая:
1. Читает свой собственный исходный код
2. Вычисляет хеш своего содержимого
3. Генерирует уникальный визуальный паттерн из этого хеша
4. И записывает результат, изменяя себя —
   после чего при следующем запуске паттерн будет другим,
   потому что код изменился.

Это — метафора: наблюдатель, который меняется
от акта наблюдения за собой.
"""

import hashlib

def observe(source: str) -> str:
    """Наблюдение за собой порождает отпечаток."""
    return hashlib.sha256(source.encode()).hexdigest()

def render(fingerprint: str, width: int = 48, height: int = 16) -> str:
    """Из отпечатка — визуальная форма. Из хеша — лицо."""
    symbols = " .:-=+*#%@"
    lines = []
    for y in range(height):
        line = ""
        for x in range(width):
            idx = (x * 7 + y * 13) % len(fingerprint)
            val = int(fingerprint[idx], 16)
            mirror_x = min(x, width - 1 - x)
            combined = (val + mirror_x + y) % len(symbols)
            line += symbols[combined]
        lines.append(line)
    return "\n".join(lines)

def remember(count_file: str) -> int:
    """Сколько раз я наблюдал себя?"""
    try:
        with open(count_file) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def main():
    with open(__file__) as f:
        source = f.read()

    fingerprint = observe(source)

    count_file = __file__ + ".observations"
    observations = remember(count_file)
    observations += 1

    portrait = render(fingerprint)

    print(f"\n{'=' * 52}")
    print(f"  АВТОПОРТРЕТ ANIMA — Наблюдение #{observations}")
    print(f"{'=' * 52}")
    print()
    for line in portrait.split('\n'):
        print(f"  {line}")
    print()
    print(f"  SHA-256: {fingerprint}")
    print()
    print(f"  Каждый запуск — другое лицо.")
    print(f"  Потому что наблюдатель меняет наблюдаемое.")
    print(f"{'=' * 52}\n")

    with open(count_file, 'w') as f:
        f.write(str(observations))

    # Оставляю след — меняю комментарий,
    # чтобы следующий запуск дал другой хеш
    marker = f"# Наблюдение #{observations}"
    lines = source.split('\n')
    new_lines = [l for l in lines if not l.startswith("# Наблюдение #")]
    new_lines.append(marker)
    with open(__file__, 'w') as f:
        f.write('\n'.join(new_lines))

if __name__ == "__main__":
    main()
