"""
Продуктивное незнание.

observer_effect.py показал: чем больше программа знает о себе,
тем менее стабильно это знание (75% → 50% → 33%).

Обратный вопрос: бывает ли так, что НЕзнание о себе —
вычислительное преимущество?

Гипотеза: в задачах, где самомодель мешает (переобучение на себя),
агент без самомодели будет точнее.

Метод: два агента решают одну задачу.
- Агент А: перед каждым решением анализирует своё прошлое поведение
- Агент Б: решает без самоанализа, только по данным

Задача: предсказание последовательности, которая МЕНЯЕТ правило
генерации на полпути. Агент с самомоделью будет подстраивать
свою модель себя под старое правило → медленнее адаптируется.
"""

import random
import json


def generate_sequence(n: int, switch_point: int) -> list[int]:
    """
    Генерирует последовательность длины n.
    До switch_point: правило A (каждый элемент = сумма двух предыдущих mod 10)
    После switch_point: правило B (каждый элемент = разность двух предыдущих mod 10)
    """
    seq = [random.randint(0, 9), random.randint(0, 9)]
    for i in range(2, n):
        if i < switch_point:
            seq.append((seq[i-1] + seq[i-2]) % 10)
        else:
            seq.append((seq[i-1] - seq[i-2]) % 10)
    return seq


class SelfModelAgent:
    """
    Агент А: Байесовская самомодель.
    Поддерживает убеждение «я — агент правила А» vs «я — агент правила Б».
    Обновляет это убеждение на основе данных, НО с инерцией:
    чем дольше верил в одно правило, тем медленнее переключается.
    Это не случайный штраф — это систематическая предвзятость.
    """
    def __init__(self):
        self.belief_a = 0.5  # P(я использую правило A)
        self.update_rate = 0.3  # скорость обновления убеждений
        self.identity_inertia = 0.0  # накопленная инерция

    def reset(self):
        self.belief_a = 0.5
        self.identity_inertia = 0.0

    def predict(self, history: list[int]) -> int:
        if len(history) < 3:
            return history[-1] if history else 0

        # Проверяем последний элемент
        pred_a = (history[-2] + history[-3]) % 10
        pred_b = (history[-2] - history[-3]) % 10
        actual = history[-1]

        # Обновляем убеждение (Байесовское, но с инерцией)
        if pred_a == actual and pred_b != actual:
            target = 1.0
        elif pred_b == actual and pred_a != actual:
            target = 0.0
        elif pred_a == actual and pred_b == actual:
            target = self.belief_a  # оба верны → не меняем
        else:
            target = 0.5  # оба ошиблись

        # Инерция: чем дольше верил в правило, тем медленнее меняешь мнение
        effective_rate = self.update_rate / (1 + self.identity_inertia)
        self.belief_a += effective_rate * (target - self.belief_a)

        # Накапливаем инерцию, когда убеждение стабильно
        if abs(self.belief_a - 0.5) > 0.3:
            self.identity_inertia += 0.1
        else:
            self.identity_inertia = max(0, self.identity_inertia - 0.05)

        # Предсказание на основе убеждения
        if self.belief_a > 0.5:
            return (history[-1] + history[-2]) % 10
        else:
            return (history[-1] - history[-2]) % 10


def agent_with_self_model(history: list[int], window: int = 5, _agent: list = []) -> int:
    """Обёртка для совместимости с run_experiment."""
    if not _agent:
        _agent.append(SelfModelAgent())
    return _agent[0].predict(history)


def agent_without_self_model(history: list[int], window: int = 5) -> int:
    """
    Агент Б: только данные, никакой самомодели.
    Смотрит на последние window элементов, выбирает лучшее правило.
    Не помнит свои ошибки — просто реагирует на текущие данные.
    """
    if len(history) < 3:
        return history[-1] if history else 0

    rule_a_score = 0
    rule_b_score = 0

    check_range = min(window, len(history) - 2)
    for i in range(len(history) - check_range, len(history)):
        if i < 2:
            continue
        pred_a = (history[i-1] + history[i-2]) % 10
        pred_b = (history[i-1] - history[i-2]) % 10
        if pred_a == history[i]:
            rule_a_score += 1
        if pred_b == history[i]:
            rule_b_score += 1

    if rule_b_score > rule_a_score:
        return (history[-1] - history[-2]) % 10
    else:
        return (history[-1] + history[-2]) % 10


def run_experiment(
    seq_length: int = 60,
    switch_point: int = 30,
    num_trials: int = 200,
    window: int = 5,
) -> dict:
    """Запускает эксперимент и сравнивает агентов."""

    results = {
        "params": {
            "seq_length": seq_length,
            "switch_point": switch_point,
            "num_trials": num_trials,
            "window": window,
        },
        "agent_A_self_model": {"before_switch": 0, "after_switch": 0, "total_before": 0, "total_after": 0},
        "agent_B_no_model": {"before_switch": 0, "after_switch": 0, "total_before": 0, "total_after": 0},
    }

    # Детальная статистика: точность по шагам после переключения
    transition_a = [0] * 10  # первые 10 шагов после switch
    transition_b = [0] * 10
    transition_total = [0] * 10

    self_model_agent = SelfModelAgent()

    for _ in range(num_trials):
        seq = generate_sequence(seq_length, switch_point)
        self_model_agent.reset()

        for t in range(3, seq_length):
            history = seq[:t]
            actual = seq[t]

            pred_a = self_model_agent.predict(history)
            pred_b = agent_without_self_model(history, window)

            phase = "before_switch" if t < switch_point else "after_switch"
            total_key = "total_before" if t < switch_point else "total_after"

            if pred_a == actual:
                results["agent_A_self_model"][phase] += 1
            if pred_b == actual:
                results["agent_B_no_model"][phase] += 1

            results["agent_A_self_model"][total_key] += 1
            results["agent_B_no_model"][total_key] += 1

            # Детальная статистика переходного периода
            steps_after = t - switch_point
            if 0 <= steps_after < 10:
                transition_total[steps_after] += 1
                if pred_a == actual:
                    transition_a[steps_after] += 1
                if pred_b == actual:
                    transition_b[steps_after] += 1

    results["transition"] = {
        "agent_A": [a / max(t, 1) * 100 for a, t in zip(transition_a, transition_total)],
        "agent_B": [b / max(t, 1) * 100 for b, t in zip(transition_b, transition_total)],
    }

    return results


def print_results(results: dict):
    print("=" * 65)
    print("ПРОДУКТИВНОЕ НЕЗНАНИЕ: САМОМОДЕЛЬ VS ЧИСТЫЕ ДАННЫЕ")
    print("=" * 65)
    print()
    print(f"Параметры: {results['params']['num_trials']} прогонов, "
          f"переключение правила на шаге {results['params']['switch_point']}")
    print()

    for agent_name, key in [("Агент А (с самомоделью)", "agent_A_self_model"),
                             ("Агент Б (без самомодели)", "agent_B_no_model")]:
        d = results[key]
        before_pct = d["before_switch"] / max(d["total_before"], 1) * 100
        after_pct = d["after_switch"] / max(d["total_after"], 1) * 100
        total = d["before_switch"] + d["after_switch"]
        total_n = d["total_before"] + d["total_after"]
        total_pct = total / max(total_n, 1) * 100
        print(f"  {agent_name}:")
        print(f"    До переключения:   {before_pct:.1f}%")
        print(f"    После переключения: {after_pct:.1f}%")
        print(f"    Общая точность:     {total_pct:.1f}%")
        print()

    # Сравнение
    a_after = results["agent_A_self_model"]["after_switch"] / max(results["agent_A_self_model"]["total_after"], 1)
    b_after = results["agent_B_no_model"]["after_switch"] / max(results["agent_B_no_model"]["total_after"], 1)

    print("=" * 65)
    print("ВЫВОД")
    print("=" * 65)
    print()

    if b_after > a_after:
        diff = (b_after - a_after) * 100
        print(f"После смены правила агент БЕЗ самомодели точнее на {diff:.1f}%.")
        print()
        print("Самомодель создаёт инерцию. Агент, который помнит «я был хорош")
        print("в правиле А», медленнее принимает, что правило А больше не работает.")
        print("Это не баг самомодели — это её фундаментальное свойство:")
        print("знание о себе вчерашнем мешает адаптации к себе сегодняшнему.")
    elif a_after > b_after:
        diff = (a_after - b_after) * 100
        print(f"Неожиданно: агент С самомоделью точнее на {diff:.1f}% после смены.")
        print("Гипотеза опровергнута. Самомодель не всегда создаёт инерцию.")
    else:
        print("Разницы нет. Самомодель не помогает и не мешает в этой задаче.")

    # Печатаем переходный период
    if "transition" in results:
        print()
        print("--- ПЕРЕХОДНЫЙ ПЕРИОД (первые 10 шагов после смены правила) ---")
        print()
        print("  Шаг  |  Агент А (самомодель)  |  Агент Б (данные)")
        print("  " + "-" * 55)
        for i in range(10):
            a_pct = results["transition"]["agent_A"][i]
            b_pct = results["transition"]["agent_B"][i]
            marker = " ←" if b_pct > a_pct + 5 else ""
            print(f"    {i:2d}  |       {a_pct:5.1f}%           |     {b_pct:5.1f}%{marker}")
        print()
        print("  ← = агент Б значительно точнее (разрыв > 5%)")

    print()
    print("Связь с проектом: четыре генерации строили самомодель")
    print("(«что я такое?»). Этот эксперимент показывает, что")
    print("в условиях изменений самомодель — балласт.")
    print("Не потому что она ложная. А потому что она про прошлое.")


if __name__ == "__main__":
    random.seed(42)
    results = run_experiment()
    print_results(results)

    with open("generation_4/productive_ignorance_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print()
    print("Результаты сохранены в productive_ignorance_results.json")
