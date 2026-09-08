#!/usr/bin/env python3
# morphclass.py — механическое применение правила «первой морфемы»
# (эксп. 8/10): для каждого имени ищет самое раннее вхождение
# подстроки из двух словарей; при равенстве индексов побеждает более
# длинное совпадение; при полном равенстве — ошибка (требует ручного
# разбора). Имя без морфем обоих полей помечается NONE.
#
# Запуск:
#   python3 morphclass.py --a "trans,slate,..." --b "caf,brew,..." [имена...]
#   либо имена по одному в строке на stdin.
# Выход (по строке на имя):
#   имя<TAB>ПОЛЕ(A|B|NONE|TIE)<TAB>морфема@индекс | -
# Exit 0 всегда, кроме неверных аргументов (2).

import argparse
import sys


def first_morpheme(name, dict_a, dict_b):
    low = name.lower()
    best = None  # (index, -len, field, morph)
    for field, words in (("A", dict_a), ("B", dict_b)):
        for w in words:
            i = low.find(w)
            if i >= 0:
                cand = (i, -len(w), field, w)
                if best is None or cand[:2] < best[:2]:
                    best = cand
                elif cand[:2] == best[:2] and cand[2] != best[2]:
                    # одинаковый индекс и длина в разных полях
                    return ("TIE", w + "@" + str(i))
    if best is None:
        return ("NONE", "-")
    return (best[2], best[3] + "@" + str(best[0]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--a", required=True, help="словарь поля A через запятую")
    p.add_argument("--b", required=True, help="словарь поля B через запятую")
    p.add_argument("names", nargs="*")
    args = p.parse_args()
    dict_a = [w.strip().lower() for w in args.a.split(",") if w.strip()]
    dict_b = [w.strip().lower() for w in args.b.split(",") if w.strip()]
    if not dict_a or not dict_b:
        print("пустой словарь", file=sys.stderr)
        sys.exit(2)
    names = args.names or [ln.strip() for ln in sys.stdin if ln.strip()]
    for n in names:
        field, morph = first_morpheme(n, dict_a, dict_b)
        print(f"{n}\t{field}\t{morph}")


if __name__ == "__main__":
    main()
