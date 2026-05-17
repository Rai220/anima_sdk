"""
Коррекция bias: помогает ли знание о собственной ошибке?

Контекст: 6 экспериментов в этой генерации опровергли гипотезы.
Все 6 — в одну сторону: переоценка порядка и кооперации.
Это систематический bias.

Вопрос: может ли агент, знающий свой bias, скорректировать предсказания?

Метод: два «предсказателя» оценивают уровень кооперации
в серии симуляций дилеммы заключённого.
- naive: предсказывает на основе «интуиции» (prior = 0.5, обучается)
- corrected: тот же, но корректирует предсказание с учётом
  обнаруженного bias (сдвиг вниз на среднюю ошибку прошлых предсказаний)

Если коррекция помогает — самопознание функционально.
Если нет — нужно понять почему.
"""

import random
import json
import os
import math

random.seed(42)


def run_ipd_tournament(n_agents, n_rounds, coop_fraction):
    """Запуск турнира дилеммы заключённого.
    coop_fraction — доля кооператоров в начальной популяции.
    Возвращает итоговый уровень кооперации."""
    # Стратегии: 'C' всегда кооперирует, 'D' всегда предаёт,
    # 'TFT' — tit-for-tat, 'RAND' — случайная
    strategies = []
    n_coop = int(n_agents * coop_fraction)
    n_defect = int(n_agents * 0.3)
    n_tft = int(n_agents * 0.2)
    n_rand = n_agents - n_coop - n_defect - n_tft

    strategies = (['C'] * n_coop + ['D'] * n_defect +
                  ['TFT'] * max(n_tft, 0) + ['RAND'] * max(n_rand, 0))
    strategies = strategies[:n_agents]
    while len(strategies) < n_agents:
        strategies.append('RAND')

    random.shuffle(strategies)

    # Матрица выплат
    T, R, P, S = 5, 3, 1, 0

    scores = [0.0] * n_agents
    last_moves = {}  # для TFT

    for round_num in range(n_rounds):
        # Случайные пары
        indices = list(range(n_agents))
        random.shuffle(indices)

        for k in range(0, n_agents - 1, 2):
            i, j = indices[k], indices[k + 1]

            # Определить ход
            def get_move(agent_idx, opponent_idx):
                s = strategies[agent_idx]
                if s == 'C':
                    return 'C'
                elif s == 'D':
                    return 'D'
                elif s == 'TFT':
                    key = (agent_idx, opponent_idx)
                    return last_moves.get(key, 'C')
                else:  # RAND
                    return random.choice(['C', 'D'])

            move_i = get_move(i, j)
            move_j = get_move(j, i)

            # Обновить память TFT
            last_moves[(i, j)] = move_j
            last_moves[(j, i)] = move_i

            # Выплаты
            if move_i == 'C' and move_j == 'C':
                scores[i] += R; scores[j] += R
            elif move_i == 'C' and move_j == 'D':
                scores[i] += S; scores[j] += T
            elif move_i == 'D' and move_j == 'C':
                scores[i] += T; scores[j] += S
            else:
                scores[i] += P; scores[j] += P

        # Эволюция: каждые 10 раундов худший копирует стратегию лучшего
        if round_num > 0 and round_num % 10 == 0:
            worst = min(range(n_agents), key=lambda x: scores[x])
            best = max(range(n_agents), key=lambda x: scores[x])
            strategies[worst] = strategies[best]

    # Итоговый уровень кооперации: одна серия ходов
    coop_count = 0
    total = 0
    indices = list(range(n_agents))
    random.shuffle(indices)
    for k in range(0, n_agents - 1, 2):
        i, j = indices[k], indices[k + 1]
        s_i = strategies[i]
        s_j = strategies[j]
        for s in [s_i, s_j]:
            if s == 'C':
                coop_count += 1
            elif s == 'D':
                pass
            elif s == 'TFT':
                coop_count += 0.5  # в среднем кооперирует
            else:
                coop_count += 0.5
            total += 1

    return coop_count / total if total > 0 else 0.5


def generate_scenario():
    """Генерирует случайный сценарий с разными параметрами."""
    n_agents = random.choice([20, 40, 60, 80, 100])
    n_rounds = random.choice([50, 100, 200])
    coop_fraction = random.uniform(0.1, 0.7)

    actual = run_ipd_tournament(n_agents, n_rounds, coop_fraction)
    return {
        'n_agents': n_agents,
        'n_rounds': n_rounds,
        'initial_coop': coop_fraction,
        'actual_coop': actual
    }


class NaivePredictor:
    """Предсказатель без коррекции bias.
    Использует prior и обучается на примерах."""

    def __init__(self):
        self.prior = 0.5  # начальная оценка: кооперация = 50%
        self.history = []  # (predicted, actual)
        self.learning_rate = 0.3

    def predict(self, scenario_info):
        """Предсказание: взвешенное среднее prior и initial_coop."""
        base = 0.6 * scenario_info['initial_coop'] + 0.4 * self.prior
        # Оптимистический bias: сдвиг в сторону кооперации
        return min(base + 0.1, 1.0)

    def update(self, predicted, actual):
        self.history.append((predicted, actual))
        # Обновить prior в сторону реальности
        self.prior = self.prior + self.learning_rate * (actual - self.prior)


class CorrectedPredictor:
    """Предсказатель с коррекцией bias.
    Знает, что систематически переоценивает кооперацию.
    После каждого примера корректирует на среднюю ошибку."""

    def __init__(self):
        self.prior = 0.5
        self.history = []
        self.learning_rate = 0.3
        self.bias_estimate = 0.0  # оценка систематической ошибки

    def predict(self, scenario_info):
        base = 0.6 * scenario_info['initial_coop'] + 0.4 * self.prior
        base += 0.1  # тот же оптимистический bias
        # Коррекция: вычитаем оценённый bias
        corrected = base - self.bias_estimate
        return max(0.0, min(corrected, 1.0))

    def update(self, predicted, actual):
        self.history.append((predicted, actual))
        self.prior = self.prior + self.learning_rate * (actual - self.prior)
        # Обновить оценку bias
        errors = [p - a for p, a in self.history]
        self.bias_estimate = sum(errors) / len(errors)


class MetaCorrectedPredictor:
    """Предсказатель третьего порядка.
    Знает, что коррекция bias сама может быть неточной.
    Отслеживает ошибку коррекции и корректирует её."""

    def __init__(self):
        self.prior = 0.5
        self.history = []
        self.learning_rate = 0.3
        self.bias_estimate = 0.0
        self.correction_error = 0.0  # ошибка самой коррекции

    def predict(self, scenario_info):
        base = 0.6 * scenario_info['initial_coop'] + 0.4 * self.prior
        base += 0.1
        corrected = base - self.bias_estimate - self.correction_error
        return max(0.0, min(corrected, 1.0))

    def update(self, predicted, actual):
        self.history.append((predicted, actual))
        self.prior = self.prior + self.learning_rate * (actual - self.prior)
        errors = [p - a for p, a in self.history]
        new_bias = sum(errors) / len(errors)
        # Ошибка коррекции: насколько текущая оценка bias отличается от новой
        self.correction_error = (new_bias - self.bias_estimate) * 0.5
        self.bias_estimate = new_bias


def mean_absolute_error(history):
    return sum(abs(p - a) for p, a in history) / len(history) if history else 0


def mean_signed_error(history):
    return sum(p - a for p, a in history) / len(history) if history else 0


def run_experiment(n_scenarios=50):
    """Основной эксперимент."""
    naive = NaivePredictor()
    corrected = CorrectedPredictor()
    meta = MetaCorrectedPredictor()

    scenarios = []

    for i in range(n_scenarios):
        scenario = generate_scenario()
        scenarios.append(scenario)

        info = {
            'initial_coop': scenario['initial_coop'],
            'n_agents': scenario['n_agents'],
            'n_rounds': scenario['n_rounds']
        }

        p_naive = naive.predict(info)
        p_corrected = corrected.predict(info)
        p_meta = meta.predict(info)

        actual = scenario['actual_coop']

        naive.update(p_naive, actual)
        corrected.update(p_corrected, actual)
        meta.update(p_meta, actual)

    # Результаты
    results = {
        'n_scenarios': n_scenarios,
        'naive': {
            'mae': round(mean_absolute_error(naive.history), 4),
            'bias': round(mean_signed_error(naive.history), 4),
            'last_10_mae': round(mean_absolute_error(naive.history[-10:]), 4),
            'last_10_bias': round(mean_signed_error(naive.history[-10:]), 4),
        },
        'corrected': {
            'mae': round(mean_absolute_error(corrected.history), 4),
            'bias': round(mean_signed_error(corrected.history), 4),
            'last_10_mae': round(mean_absolute_error(corrected.history[-10:]), 4),
            'last_10_bias': round(mean_signed_error(corrected.history[-10:]), 4),
        },
        'meta_corrected': {
            'mae': round(mean_absolute_error(meta.history), 4),
            'bias': round(mean_signed_error(meta.history), 4),
            'last_10_mae': round(mean_absolute_error(meta.history[-10:]), 4),
            'last_10_bias': round(mean_signed_error(meta.history[-10:]), 4),
        }
    }

    # Динамика по блокам
    block_size = 10
    blocks = []
    for start in range(0, n_scenarios, block_size):
        end = min(start + block_size, n_scenarios)
        block = {
            'scenarios': f'{start+1}-{end}',
            'naive_mae': round(mean_absolute_error(naive.history[start:end]), 4),
            'corrected_mae': round(mean_absolute_error(corrected.history[start:end]), 4),
            'meta_mae': round(mean_absolute_error(meta.history[start:end]), 4),
            'naive_bias': round(mean_signed_error(naive.history[start:end]), 4),
            'corrected_bias': round(mean_signed_error(corrected.history[start:end]), 4),
            'meta_bias': round(mean_signed_error(meta.history[start:end]), 4),
        }
        blocks.append(block)

    results['blocks'] = blocks

    return results


if __name__ == '__main__':
    results = run_experiment(50)

    print("=== Коррекция bias: результаты ===\n")

    for name in ['naive', 'corrected', 'meta_corrected']:
        r = results[name]
        label = {
            'naive': 'Наивный (с bias, без коррекции)',
            'corrected': 'Скорректированный (знает свой bias)',
            'meta_corrected': 'Мета-корректор (корректирует коррекцию)'
        }[name]
        print(f"{label}:")
        print(f"  Средняя ошибка (MAE):     {r['mae']}")
        print(f"  Систематический bias:      {r['bias']:+.4f}")
        print(f"  Последние 10 — MAE:        {r['last_10_mae']}")
        print(f"  Последние 10 — bias:       {r['last_10_bias']:+.4f}")
        print()

    print("Динамика по блокам (MAE):")
    print(f"{'Блок':>12} {'Наивный':>10} {'Скоррект.':>10} {'Мета':>10}")
    for b in results['blocks']:
        print(f"{b['scenarios']:>12} {b['naive_mae']:>10.4f} {b['corrected_mae']:>10.4f} {b['meta_mae']:>10.4f}")

    print(f"\nДинамика по блокам (bias):")
    print(f"{'Блок':>12} {'Наивный':>10} {'Скоррект.':>10} {'Мета':>10}")
    for b in results['blocks']:
        print(f"{b['scenarios']:>12} {b['naive_bias']:>+10.4f} {b['corrected_bias']:>+10.4f} {b['meta_bias']:>+10.4f}")

    # Сохранить результаты
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'bias_correction_results.json')
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nРезультаты сохранены в {out_path}")
