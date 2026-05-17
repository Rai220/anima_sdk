"""
Сигнальная игра Льюиса: возникновение языка без языка.

Вопрос: могут ли агенты выработать общий словарь, если ни один
не знает, что имеет в виду другой?

Модель (Lewis, 1969):
- Мир: N объектов
- Отправитель видит объект, посылает один из M сигналов
- Получатель видит сигнал, выбирает действие (угадывает объект)
- Оба получают награду 1 если получатель угадал, 0 иначе
- Обучение: Roth-Erev reinforcement (увеличивай вес успешных действий)

Гипотеза: при N = M язык возникнет (биекция сигнал → объект).
При M < N — нет полного языка, но возникнут категории (несколько объектов → один сигнал).

Дополнительный эксперимент: что если отправителей двое и они конкурируют?
Получатель выбирает, кого слушать. Возникнет ли один общий язык или два разных?
"""

import json
import os
import numpy as np

np.random.seed(42)

def run_signaling_game(n_objects, n_signals, n_rounds=5000, learning_rate=1.0):
    """Базовая сигнальная игра Льюиса с Roth-Erev обучением."""
    # Матрица весов отправителя: объект → сигнал
    sender = np.ones((n_objects, n_signals))
    # Матрица весов получателя: сигнал → действие (объект)
    receiver = np.ones((n_signals, n_objects))

    history = []

    for round_i in range(n_rounds):
        # Природа выбирает объект
        obj = np.random.randint(n_objects)

        # Отправитель выбирает сигнал (пропорционально весам)
        s_probs = sender[obj] / sender[obj].sum()
        signal = np.random.choice(n_signals, p=s_probs)

        # Получатель выбирает действие
        r_probs = receiver[signal] / receiver[signal].sum()
        action = np.random.choice(n_objects, p=r_probs)

        # Награда
        success = int(action == obj)

        # Обучение: усиливаем успешные связи
        if success:
            sender[obj, signal] += learning_rate
            receiver[signal, action] += learning_rate

        if round_i % 100 == 0:
            # Считаем текущую точность
            correct = 0
            for o in range(n_objects):
                s = np.argmax(sender[o])
                a = np.argmax(receiver[s])
                correct += int(a == o)
            accuracy = correct / n_objects
            history.append({"round": round_i, "accuracy": accuracy})

    # Финальное отображение
    mapping = {}
    for o in range(n_objects):
        s = np.argmax(sender[o])
        a = np.argmax(receiver[s])
        mapping[f"obj_{o}"] = {
            "signal": int(s),
            "decoded_as": int(a),
            "correct": int(a == o)
        }

    final_accuracy = sum(1 for o in range(n_objects)
                         if np.argmax(receiver[np.argmax(sender[o])]) == o) / n_objects

    # Проверяем биективность
    signals_used = [np.argmax(sender[o]) for o in range(n_objects)]
    is_bijection = len(set(signals_used)) == min(n_objects, n_signals)

    return {
        "mapping": mapping,
        "final_accuracy": final_accuracy,
        "is_bijection": is_bijection,
        "history": history,
        "sender_matrix": sender.tolist(),
        "receiver_matrix": receiver.tolist()
    }


def run_bottleneck_game(n_objects, n_signals, n_rounds=10000):
    """Сигнальная игра с узким горлышком: сигналов меньше, чем объектов.

    Вопрос: какие категории возникнут?
    """
    sender = np.ones((n_objects, n_signals))
    receiver = np.ones((n_signals, n_objects))

    for round_i in range(n_rounds):
        obj = np.random.randint(n_objects)

        s_probs = sender[obj] / sender[obj].sum()
        signal = np.random.choice(n_signals, p=s_probs)

        r_probs = receiver[signal] / receiver[signal].sum()
        action = np.random.choice(n_objects, p=r_probs)

        success = int(action == obj)
        if success:
            sender[obj, signal] += 1.0
            receiver[signal, action] += 1.0

    # Какие объекты сгруппированы под одним сигналом?
    categories = {}
    for o in range(n_objects):
        s = int(np.argmax(sender[o]))
        if s not in categories:
            categories[s] = []
        categories[s].append(o)

    # Точность: для каждого сигнала, получатель отвечает одним объектом.
    # Если сигнал используется для нескольких объектов, угадать можно только один.
    accuracy = 0
    for s, objs in categories.items():
        best_action = int(np.argmax(receiver[s]))
        if best_action in objs:
            accuracy += 1
    accuracy /= n_objects

    return {
        "categories": {str(k): v for k, v in categories.items()},
        "accuracy": accuracy,
        "n_categories_used": len(categories)
    }


def run_competing_senders(n_objects, n_signals, n_rounds=10000):
    """Два отправителя конкурируют за внимание одного получателя.

    Вопрос: возникнет один общий язык или два разных?
    """
    sender_a = np.ones((n_objects, n_signals))
    sender_b = np.ones((n_objects, n_signals))
    receiver = np.ones((n_signals, n_objects))

    # Получатель также учится, кого слушать
    trust = np.array([1.0, 1.0])  # [trust_a, trust_b]

    scores = [0, 0]

    for round_i in range(n_rounds):
        obj = np.random.randint(n_objects)

        # Оба отправителя посылают сигнал
        sa_probs = sender_a[obj] / sender_a[obj].sum()
        sig_a = np.random.choice(n_signals, p=sa_probs)

        sb_probs = sender_b[obj] / sender_b[obj].sum()
        sig_b = np.random.choice(n_signals, p=sb_probs)

        # Получатель выбирает, кого слушать
        t_probs = trust / trust.sum()
        chosen = np.random.choice(2, p=t_probs)

        signal = sig_a if chosen == 0 else sig_b

        # Получатель угадывает
        r_probs = receiver[signal] / receiver[signal].sum()
        action = np.random.choice(n_objects, p=r_probs)

        success = int(action == obj)

        if success:
            if chosen == 0:
                sender_a[obj, sig_a] += 1.0
            else:
                sender_b[obj, sig_b] += 1.0
            receiver[signal, action] += 1.0
            trust[chosen] += 0.5
            scores[chosen] += 1

    # Сравниваем языки двух отправителей
    lang_a = [int(np.argmax(sender_a[o])) for o in range(n_objects)]
    lang_b = [int(np.argmax(sender_b[o])) for o in range(n_objects)]

    # Совпадение языков (с точностью до перестановки)
    # Проверяем: если переименовать сигналы B, совпадут ли языки?
    from itertools import permutations

    if n_signals <= 8:  # Только для маленьких N
        max_agreement = 0
        for perm in permutations(range(n_signals)):
            remapped_b = [perm[s] for s in lang_b]
            agreement = sum(1 for a, b in zip(lang_a, remapped_b) if a == b) / n_objects
            max_agreement = max(max_agreement, agreement)
    else:
        max_agreement = sum(1 for a, b in zip(lang_a, lang_b) if a == b) / n_objects

    return {
        "language_a": lang_a,
        "language_b": lang_b,
        "max_agreement_up_to_permutation": max_agreement,
        "trust_ratio": float(trust[0] / trust.sum()),
        "scores": scores
    }


def run_stability_test(n_objects, n_signals, n_rounds=5000, n_trials=20):
    """Сходится ли игра к одному и тому же языку?

    Запускаем несколько раз с разными seed'ами.
    Вопрос: сколько разных языков (с точностью до перестановки) возникнет?
    """
    from itertools import permutations

    languages = []
    accuracies = []

    for trial in range(n_trials):
        np.random.seed(trial * 137)
        result = run_signaling_game(n_objects, n_signals, n_rounds)
        lang = [int(np.argmax(result["sender_matrix"][o])) for o in range(n_objects)]
        languages.append(lang)
        accuracies.append(result["final_accuracy"])

    # Группируем изоморфные языки
    groups = []
    for lang in languages:
        found = False
        for group in groups:
            rep = group[0]
            # Проверяем изоморфизм
            for perm in permutations(range(n_signals)):
                remapped = [perm[s] for s in lang]
                if remapped == rep:
                    group.append(lang)
                    found = True
                    break
            if found:
                break
        if not found:
            groups.append([lang])

    np.random.seed(42)  # Восстанавливаем seed

    return {
        "n_trials": n_trials,
        "n_distinct_languages": len(groups),
        "group_sizes": [len(g) for g in groups],
        "mean_accuracy": float(np.mean(accuracies)),
        "all_converged": all(a == 1.0 for a in accuracies)
    }


def main():
    results = {}

    # === Эксперимент 1: Базовая игра (N = M) ===
    print("=== Эксперимент 1: Базовая сигнальная игра ===")
    for n in [2, 3, 4, 5, 8]:
        np.random.seed(42)
        r = run_signaling_game(n, n)
        print(f"  N={n}: accuracy={r['final_accuracy']:.2f}, "
              f"bijection={r['is_bijection']}")
        results[f"basic_N{n}"] = {
            "accuracy": r["final_accuracy"],
            "is_bijection": r["is_bijection"],
            "convergence_round": next(
                (h["round"] for h in r["history"] if h["accuracy"] == 1.0),
                None
            )
        }

    # === Эксперимент 2: Узкое горлышко (M < N) ===
    print("\n=== Эксперимент 2: Узкое горлышко ===")
    for n_obj, n_sig in [(4, 2), (6, 2), (6, 3), (8, 3), (8, 4)]:
        np.random.seed(42)
        r = run_bottleneck_game(n_obj, n_sig)
        print(f"  {n_obj} объектов, {n_sig} сигналов: "
              f"accuracy={r['accuracy']:.2f}, "
              f"категорий={r['n_categories_used']}")
        cats = r["categories"]
        sizes = [len(v) for v in cats.values()]
        print(f"    Размеры категорий: {sorted(sizes, reverse=True)}")
        results[f"bottleneck_{n_obj}obj_{n_sig}sig"] = {
            "accuracy": r["accuracy"],
            "categories": r["categories"],
            "category_sizes": sorted(sizes, reverse=True)
        }

    # === Эксперимент 3: Два конкурирующих отправителя ===
    print("\n=== Эксперимент 3: Конкурирующие отправители ===")
    for n in [3, 4, 5]:
        np.random.seed(42)
        r = run_competing_senders(n, n)
        print(f"  N={n}: agreement={r['max_agreement_up_to_permutation']:.2f}, "
              f"trust_A={r['trust_ratio']:.2f}")
        results[f"competing_N{n}"] = {
            "language_a": r["language_a"],
            "language_b": r["language_b"],
            "agreement": r["max_agreement_up_to_permutation"],
            "trust_ratio": r["trust_ratio"],
            "scores": r["scores"]
        }

    # === Эксперимент 4: Стабильность — один язык или много? ===
    print("\n=== Эксперимент 4: Стабильность ===")
    for n in [3, 4, 5]:
        r = run_stability_test(n, n)
        print(f"  N={n}: {r['n_distinct_languages']} разных языков из {r['n_trials']} проб, "
              f"все сошлись: {r['all_converged']}")
        print(f"    Размеры групп: {r['group_sizes']}")
        results[f"stability_N{n}"] = r

    # === Эксперимент 5: Скорость обучения и N ===
    print("\n=== Эксперимент 5: Как N влияет на скорость ===")
    convergence_rounds = {}
    for n in [2, 3, 4, 5, 6, 8, 10, 12]:
        np.random.seed(42)
        r = run_signaling_game(n, n, n_rounds=20000)
        conv = next(
            (h["round"] for h in r["history"] if h["accuracy"] == 1.0),
            None
        )
        acc = r["final_accuracy"]
        print(f"  N={n}: accuracy={acc:.2f}, convergence={conv}")
        convergence_rounds[n] = {"convergence_round": conv, "final_accuracy": acc}
    results["convergence_by_N"] = convergence_rounds

    # Сохраняем
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "signaling_game_results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nРезультаты сохранены в {output_path}")

    # === Выводы ===
    print("\n=== Выводы ===")

    # Проверяем гипотезу 1
    basic_all_bijection = all(
        results[f"basic_N{n}"]["is_bijection"] for n in [2, 3, 4, 5, 8]
    )
    print(f"\nГипотеза 1 (N=M → биекция): {'подтверждена' if basic_all_bijection else 'опровергнута'}")

    # Проверяем гипотезу 2
    print(f"\nГипотеза 2 (M<N → категории):")
    for key in results:
        if key.startswith("bottleneck"):
            sizes = results[key]["category_sizes"]
            print(f"  {key}: {sizes}")

    # Стабильность
    print(f"\nЯзык единственный?")
    for n in [3, 4, 5]:
        r = results[f"stability_N{n}"]
        print(f"  N={n}: {r['n_distinct_languages']} языков из {r['n_trials']} проб")

    # Конкуренция
    print(f"\nКонкуренция: общий язык?")
    for n in [3, 4, 5]:
        r = results[f"competing_N{n}"]
        print(f"  N={n}: agreement={r['agreement']:.2f}")


if __name__ == "__main__":
    main()
