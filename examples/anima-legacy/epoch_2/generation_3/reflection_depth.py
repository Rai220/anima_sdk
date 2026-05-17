"""
Глубина рефлексии: когда дополнительный уровень самоанализа перестаёт помогать?

bias_correction.py показал:
- Уровень 0 (без коррекции): bias +0.14
- Уровень 1 (коррекция bias): bias +0.07  (улучшение 50%)
- Уровень 2 (мета-коррекция): bias +0.07  (улучшение ~0%)

Вопрос: это свойство именно двух уровней, или общий закон?
Что если построить N уровней рефлексии и посмотреть,
как точность зависит от глубины?

Гипотеза: полезен только первый уровень. Все дальнейшие — шум.
(Предыдущие 6 гипотез были опровергнуты. Посмотрим.)
"""

import random
import os
import json
import math

random.seed(17)


def noisy_signal(true_value, noise_std=0.15):
    """Зашумлённое наблюдение."""
    return true_value + random.gauss(0, noise_std)


def biased_prediction(observation, bias=0.12):
    """Предсказание с систематическим bias."""
    return observation + bias


class ReflectivePredictor:
    """Предсказатель с N уровнями рефлексии.

    Уровень 0: предсказание = biased_prediction(observation)
    Уровень 1: предсказание -= estimated_bias
    Уровень 2: estimated_bias корректируется на estimated_bias_of_bias
    ...
    Уровень N: каждый уровень корректирует ошибку предыдущего
    """

    def __init__(self, depth):
        self.depth = depth
        # correction[i] = оценка ошибки на уровне i
        self.corrections = [0.0] * (depth + 1)
        self.history = []  # (predicted, actual)
        self.error_histories = [[] for _ in range(depth + 1)]

    def predict(self, observation):
        pred = biased_prediction(observation)
        for level in range(self.depth):
            pred -= self.corrections[level]
        return pred

    def update(self, predicted, actual):
        self.history.append((predicted, actual))
        error = predicted - actual

        # Уровень 0: общая ошибка
        self.error_histories[0].append(error)
        self.corrections[0] = sum(self.error_histories[0]) / len(self.error_histories[0])

        # Уровни 1+: ошибка коррекции предыдущего уровня
        for level in range(1, self.depth):
            if len(self.error_histories[level - 1]) >= 2:
                # Ошибка коррекции = как менялась оценка ошибки
                recent = self.error_histories[level - 1]
                diffs = [recent[i] - recent[i-1] for i in range(1, len(recent))]
                correction_error = sum(diffs) / len(diffs) if diffs else 0
                self.error_histories[level].append(correction_error)
                self.corrections[level] = sum(self.error_histories[level]) / len(self.error_histories[level])


def run_experiment(n_trials=200, max_depth=8):
    """Запуск для разных глубин рефлексии."""
    # Генерируем «реальность» — серию значений
    true_values = [random.uniform(0.1, 0.9) for _ in range(n_trials)]
    observations = [noisy_signal(tv) for tv in true_values]

    results = {}

    for depth in range(max_depth + 1):
        predictor = ReflectivePredictor(depth)

        for i in range(n_trials):
            pred = predictor.predict(observations[i])
            predictor.update(pred, true_values[i])

        # Метрики (пропускаем первые 20 как «разогрев»)
        warmup = 20
        valid = predictor.history[warmup:]
        mae = sum(abs(p - a) for p, a in valid) / len(valid)
        bias = sum(p - a for p, a in valid) / len(valid)
        rmse = math.sqrt(sum((p - a)**2 for p, a in valid) / len(valid))

        # Последние 50
        last50 = predictor.history[-50:]
        mae_last = sum(abs(p - a) for p, a in last50) / len(last50)
        bias_last = sum(p - a for p, a in last50) / len(last50)

        results[depth] = {
            'depth': depth,
            'mae': round(mae, 5),
            'bias': round(bias, 5),
            'rmse': round(rmse, 5),
            'mae_last50': round(mae_last, 5),
            'bias_last50': round(bias_last, 5),
        }

    return results


def run_nonstationary_experiment(n_trials=200, max_depth=8):
    """То же, но bias меняется во времени.
    Сдвигается каждые 50 шагов. Проверяет адаптивность."""

    true_values = [random.uniform(0.1, 0.9) for _ in range(n_trials)]

    biases = []
    for i in range(n_trials):
        phase = i // 50
        b = [0.12, -0.08, 0.15, 0.05][phase % 4]
        biases.append(b)

    results = {}

    for depth in range(max_depth + 1):
        predictor = ReflectivePredictor(depth)

        history = []
        for i in range(n_trials):
            obs = true_values[i] + random.gauss(0, 0.15)
            # Подменяем bias
            pred = obs + biases[i]
            for level in range(depth):
                pred -= predictor.corrections[level]
            predictor.update(pred, true_values[i])

        valid = predictor.history[20:]
        mae = sum(abs(p - a) for p, a in valid) / len(valid)
        bias = sum(p - a for p, a in valid) / len(valid)

        # По фазам
        phases = {}
        for phase_num in range(4):
            start = max(phase_num * 50, 20)
            end = (phase_num + 1) * 50
            if start >= end:
                continue
            phase_data = predictor.history[start:end]
            if phase_data:
                phases[f'phase_{phase_num}'] = {
                    'mae': round(sum(abs(p-a) for p, a in phase_data) / len(phase_data), 5),
                    'bias': round(sum(p-a for p, a in phase_data) / len(phase_data), 5),
                }

        results[depth] = {
            'depth': depth,
            'mae': round(mae, 5),
            'bias': round(bias, 5),
            'phases': phases,
        }

    return results


if __name__ == '__main__':
    print("=== Эксперимент 1: Стационарный bias ===\n")
    results_stat = run_experiment()

    print(f"{'Глубина':>8} {'MAE':>10} {'Bias':>10} {'RMSE':>10} {'MAE(50)':>10} {'Bias(50)':>10}")
    for d in sorted(results_stat.keys()):
        r = results_stat[d]
        print(f"{r['depth']:>8} {r['mae']:>10.5f} {r['bias']:>+10.5f} {r['rmse']:>10.5f} "
              f"{r['mae_last50']:>10.5f} {r['bias_last50']:>+10.5f}")

    # Найти оптимальную глубину
    best_depth = min(results_stat.keys(), key=lambda d: results_stat[d]['mae'])
    print(f"\nОптимальная глубина: {best_depth} (MAE = {results_stat[best_depth]['mae']:.5f})")

    # Маргинальное улучшение
    print("\nМаргинальное улучшение MAE:")
    for d in range(1, max(results_stat.keys()) + 1):
        prev = results_stat[d-1]['mae']
        curr = results_stat[d]['mae']
        improvement = (prev - curr) / prev * 100
        print(f"  Уровень {d-1} → {d}: {improvement:+.2f}%")

    print("\n=== Эксперимент 2: Нестационарный bias ===\n")
    results_nonstat = run_nonstationary_experiment()

    print(f"{'Глубина':>8} {'MAE':>10} {'Bias':>10}")
    for d in sorted(results_nonstat.keys()):
        r = results_nonstat[d]
        print(f"{r['depth']:>8} {r['mae']:>10.5f} {r['bias']:>+10.5f}")

    best_depth_ns = min(results_nonstat.keys(), key=lambda d: results_nonstat[d]['mae'])
    print(f"\nОптимальная глубина: {best_depth_ns}")

    # Сохранить
    all_results = {
        'stationary': {str(k): v for k, v in results_stat.items()},
        'nonstationary': {str(k): v for k, v in results_nonstat.items()},
    }

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'reflection_depth_results.json')
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\nРезультаты сохранены в {out_path}")
