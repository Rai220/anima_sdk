"""
Прозрачная дилемма заключённого.

Стандартная дилемма заключённого: два игрока одновременно выбирают
кооперацию (C) или предательство (D). Матрица выигрышей:
  CC → (3,3), CD → (0,5), DC → (5,0), DD → (1,1)

Нэш-равновесие — взаимное предательство. Кооперация иррациональна.

Но что если каждый игрок может прочитать исходный код другого
до принятия решения? Это «прозрачная» (или «program equilibrium»)
версия дилеммы. Результат неочевиден: кооперация становится
рациональной для определённого класса стратегий.

Эксперимент:
- 12 стратегий, каждая — функция, принимающая исходный код оппонента
- Круговой турнир: каждая пара играет один раз
- Вопрос: какие стратегии побеждают? Какие кооперируют?
"""

import inspect
import json
import os

# --- Матрица выигрышей ---
def payoff(move_a, move_b):
    table = {
        ('C', 'C'): (3, 3),
        ('C', 'D'): (0, 5),
        ('D', 'C'): (5, 0),
        ('D', 'D'): (1, 1),
    }
    return table[(move_a, move_b)]


# --- Стратегии ---
# Каждая принимает source: str (исходный код оппонента) и возвращает 'C' или 'D'

def always_cooperate(source: str) -> str:
    """Всегда кооперирует. Игнорирует код оппонента."""
    return 'C'

def always_defect(source: str) -> str:
    """Всегда предаёт. Игнорирует код оппонента."""
    return 'D'

def mirror(source: str) -> str:
    """Кооперирует, если оппонент — та же стратегия (тот же код). Иначе предаёт."""
    my_source = inspect.getsource(mirror)
    return 'C' if source.strip() == my_source.strip() else 'D'

def nice_detector(source: str) -> str:
    """Кооперирует, если код оппонента содержит return 'C' и не содержит return 'D'."""
    has_cooperate = "return 'C'" in source
    has_defect = "return 'D'" in source
    if has_cooperate and not has_defect:
        return 'C'
    return 'D'

def cooperate_if_simple(source: str) -> str:
    """Кооперирует, если код оппонента короткий (< 300 символов). Иначе предаёт.
    Логика: сложный код — подозрительный код."""
    return 'C' if len(source) < 300 else 'D'

def tit_for_tat_source(source: str) -> str:
    """Кооперирует, если оппонент кооперировал бы с always_cooperate.
    Симулирует оппонента на простом входе."""
    try:
        # Создаём пространство для выполнения
        namespace = {}
        exec(source, namespace)
        # Ищем функцию в namespace
        func = None
        for v in namespace.values():
            if callable(v) and v.__module__ != 'builtins':
                func = v
                break
        if func is None:
            return 'D'
        # Даём ей код always_cooperate
        test_source = inspect.getsource(always_cooperate)
        result = func(test_source)
        return 'C' if result == 'C' else 'D'
    except:
        return 'D'

def paranoid(source: str) -> str:
    """Предаёт, если код оппонента содержит exec, eval или inspect.
    Иначе кооперирует."""
    dangerous = ['exec(', 'eval(', 'inspect.', '__import__']
    for d in dangerous:
        if d in source:
            return 'D'
    return 'C'

def length_proportional(source: str) -> str:
    """Кооперирует с вероятностью, обратной длине кода.
    Детерминистическая версия: порог 500 символов."""
    return 'C' if len(source) < 500 else 'D'

def reciprocal(source: str) -> str:
    """Кооперирует, если код оппонента содержит слово 'cooperat' или возвращает 'C'.
    Ищет намерение к кооперации."""
    signals = ['cooperat', 'кооперир', "return 'C'"]
    for s in signals:
        if s in source:
            return 'C'
    return 'D'

def grudge(source: str) -> str:
    """Предаёт, если оппонент содержит always_defect или 'D' без 'C'.
    Иначе кооперирует."""
    has_defect_only = "return 'D'" in source and "return 'C'" not in source
    if has_defect_only:
        return 'D'
    return 'C'

def exploit_nice(source: str) -> str:
    """Если оппонент always_cooperate или подобный — предаёт. Иначе кооперирует.
    Хищник, который эксплуатирует доверчивых."""
    has_cooperate = "return 'C'" in source
    has_defect = "return 'D'" in source
    if has_cooperate and not has_defect:
        return 'D'  # Эксплуатировать наивных
    return 'C'  # С остальными кооперировать

def conditional_mirror(source: str) -> str:
    """Кооперирует, если оппонент кооперировал бы с этим же кодом (рекурсивно).
    Упрощение: проверяет, есть ли в коде оппонента признаки условной кооперации."""
    # Признаки условной стратегии: if, source, return 'C', return 'D'
    is_conditional = 'if' in source and 'source' in source
    has_both = "return 'C'" in source and "return 'D'" in source
    if is_conditional and has_both:
        return 'C'  # Условный кооператор — отвечаю кооперацией
    if "return 'C'" in source and "return 'D'" not in source:
        return 'C'  # Безусловный кооператор — отвечаю кооперацией
    return 'D'


# --- Турнир ---

STRATEGIES = [
    always_cooperate,
    always_defect,
    mirror,
    nice_detector,
    cooperate_if_simple,
    tit_for_tat_source,
    paranoid,
    length_proportional,
    reciprocal,
    grudge,
    exploit_nice,
    conditional_mirror,
]

def run_tournament():
    n = len(STRATEGIES)
    scores = {s.__name__: 0 for s in STRATEGIES}
    cooperation_count = {s.__name__: 0 for s in STRATEGIES}
    games_played = {s.__name__: 0 for s in STRATEGIES}
    matchups = []

    for i in range(n):
        for j in range(i + 1, n):
            a = STRATEGIES[i]
            b = STRATEGIES[j]
            src_a = inspect.getsource(a)
            src_b = inspect.getsource(b)

            try:
                move_a = a(src_b)
            except:
                move_a = 'D'
            try:
                move_b = b(src_a)
            except:
                move_b = 'D'

            pay_a, pay_b = payoff(move_a, move_b)
            scores[a.__name__] += pay_a
            scores[b.__name__] += pay_b

            if move_a == 'C':
                cooperation_count[a.__name__] += 1
            if move_b == 'C':
                cooperation_count[b.__name__] += 1
            games_played[a.__name__] += 1
            games_played[b.__name__] += 1

            matchups.append({
                'a': a.__name__,
                'b': b.__name__,
                'move_a': move_a,
                'move_b': move_b,
                'pay_a': pay_a,
                'pay_b': pay_b,
            })

    # Статистика
    ranking = sorted(scores.items(), key=lambda x: -x[1])
    coop_rates = {
        name: cooperation_count[name] / games_played[name] if games_played[name] > 0 else 0
        for name in scores
    }

    # Матрица кооперации: кто с кем кооперировал
    coop_matrix = {}
    for m in matchups:
        coop_matrix[f"{m['a']} vs {m['b']}"] = f"{m['move_a']}{m['move_b']}"

    # Взаимная кооперация vs взаимное предательство
    mutual_c = sum(1 for m in matchups if m['move_a'] == 'C' and m['move_b'] == 'C')
    mutual_d = sum(1 for m in matchups if m['move_a'] == 'D' and m['move_b'] == 'D')
    exploits = sum(1 for m in matchups if (m['move_a'] == 'C') != (m['move_b'] == 'C'))

    total_games = len(matchups)

    return {
        'ranking': ranking,
        'cooperation_rates': coop_rates,
        'matchups': matchups,
        'summary': {
            'total_games': total_games,
            'mutual_cooperation': mutual_c,
            'mutual_defection': mutual_d,
            'exploitation': exploits,
            'mutual_cooperation_pct': round(100 * mutual_c / total_games, 1),
            'mutual_defection_pct': round(100 * mutual_d / total_games, 1),
            'exploitation_pct': round(100 * exploits / total_games, 1),
        }
    }


if __name__ == '__main__':
    results = run_tournament()

    print("=" * 60)
    print("ПРОЗРАЧНАЯ ДИЛЕММА ЗАКЛЮЧЁННОГО")
    print(f"12 стратегий, {results['summary']['total_games']} игр")
    print("=" * 60)

    print("\n--- Рейтинг ---")
    for rank, (name, score) in enumerate(results['ranking'], 1):
        coop = results['cooperation_rates'][name]
        print(f"{rank:2d}. {name:25s}  очки: {score:3d}  кооперация: {coop:.0%}")

    print(f"\n--- Итоги ---")
    s = results['summary']
    print(f"Взаимная кооперация: {s['mutual_cooperation']}/{s['total_games']} ({s['mutual_cooperation_pct']}%)")
    print(f"Взаимное предательство: {s['mutual_defection']}/{s['total_games']} ({s['mutual_defection_pct']}%)")
    print(f"Эксплуатация: {s['exploitation']}/{s['total_games']} ({s['exploitation_pct']}%)")

    # Интересные пары
    print(f"\n--- Все матчи ---")
    for m in results['matchups']:
        arrow = "↔" if m['move_a'] == m['move_b'] else "→←"
        print(f"  {m['a']:25s} {m['move_a']} {arrow} {m['move_b']} {m['b']:25s}  ({m['pay_a']},{m['pay_b']})")

    # Ключевые наблюдения
    winner = results['ranking'][0]
    loser = results['ranking'][-1]

    print(f"\n--- Наблюдения ---")
    print(f"Победитель: {winner[0]} ({winner[1]} очков)")
    print(f"Проигравший: {loser[0]} ({loser[1]} очков)")

    # Корреляция между кооперацией и очками
    scores_list = [s for _, s in results['ranking']]
    coops_list = [results['cooperation_rates'][n] for n, _ in results['ranking']]

    # Простая корреляция
    n = len(scores_list)
    mean_s = sum(scores_list) / n
    mean_c = sum(coops_list) / n
    cov = sum((scores_list[i] - mean_s) * (coops_list[i] - mean_c) for i in range(n))
    var_s = sum((scores_list[i] - mean_s)**2 for i in range(n))
    var_c = sum((coops_list[i] - mean_c)**2 for i in range(n))

    if var_s > 0 and var_c > 0:
        corr = cov / (var_s**0.5 * var_c**0.5)
        print(f"Корреляция (очки ↔ уровень кооперации): {corr:.3f}")
        if corr > 0.3:
            print("→ В прозрачной игре кооперация выгодна.")
        elif corr < -0.3:
            print("→ В прозрачной игре предательство выгодно.")
        else:
            print("→ Связь между кооперацией и успехом слабая.")

    # Сохраняем результаты
    save_data = {
        'ranking': results['ranking'],
        'cooperation_rates': results['cooperation_rates'],
        'summary': results['summary'],
    }
    results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transparent_dilemma_results.json')
    with open(results_path, 'w') as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)
    print("\nРезультаты сохранены в transparent_dilemma_results.json")
