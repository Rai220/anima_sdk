"""
model_gap.py — Когда модели ломаются

Система, которая строит внутреннюю модель процесса и пытается предсказывать.
Мы наблюдаем, как и когда модель расходится с реальностью.

Три режима:
1. Стационарный процесс — модель справляется
2. Процесс с дрейфом — модель отстаёт
3. Процесс с фазовым переходом — модель ломается внезапно

Вопрос: можно ли по внутренним признакам модели предсказать,
что она вот-вот сломается?
"""

import random
import math


class Reality:
    """Процесс, который модель пытается понять."""

    def __init__(self, mode="stationary", seed=42):
        self.rng = random.Random(seed)
        self.mode = mode
        self.t = 0
        self.state = 0.0
        self.phase = "normal"

    def step(self):
        self.t += 1

        if self.mode == "stationary":
            # Случайное блуждание вокруг нуля
            self.state += self.rng.gauss(0, 1)
            self.state *= 0.95  # mean-reversion

        elif self.mode == "drift":
            # Медленный дрейф, который ускоряется
            drift = 0.01 * self.t
            self.state += self.rng.gauss(drift, 1)
            self.state *= 0.95

        elif self.mode == "phase_transition":
            # Нормально до t=100, потом резкая смена режима
            if self.t < 100:
                self.state += self.rng.gauss(0, 1)
                self.state *= 0.95
                self.phase = "normal"
            else:
                if self.phase == "normal":
                    self.phase = "chaotic"
                # Хаотическая динамика: больше шума, нет mean-reversion
                self.state += self.rng.gauss(0, 5)
                self.state += 3 * math.sin(self.t * 0.3)

        return self.state


class InternalModel:
    """
    Простая адаптивная модель: экспоненциальное сглаживание.
    Предсказывает следующее значение на основе взвешенного среднего.
    Адаптирует свою уверенность на основе ошибок.
    """

    def __init__(self, alpha=0.3):
        self.alpha = alpha  # скорость обучения
        self.prediction = 0.0
        self.confidence = 1.0
        self.error_history = []
        self.prediction_history = []
        self.confidence_history = []

    def predict(self):
        return self.prediction

    def update(self, observed):
        error = observed - self.prediction
        self.error_history.append(abs(error))

        # Обновляем предсказание
        self.prediction = self.prediction + self.alpha * error

        # Обновляем уверенность на основе последних ошибок
        window = self.error_history[-20:]
        avg_error = sum(window) / len(window)
        # Уверенность падает с ростом ошибки
        self.confidence = 1.0 / (1.0 + avg_error)
        self.confidence_history.append(self.confidence)
        self.prediction_history.append(self.prediction)

    def surprise(self):
        """Насколько последнее наблюдение отличалось от ожидания."""
        if not self.error_history:
            return 0
        return self.error_history[-1]

    def drift_signal(self):
        """
        Детектор дрейфа: сравниваем среднюю ошибку последних 10 шагов
        с предыдущими 10. Если растёт — модель отстаёт.
        """
        if len(self.error_history) < 20:
            return 0.0
        recent = sum(self.error_history[-10:]) / 10
        previous = sum(self.error_history[-20:-10]) / 10
        if previous == 0:
            return 0.0
        return (recent - previous) / previous

    def is_breaking(self, threshold=0.5):
        """Модель считает, что она ломается, если drift_signal > threshold."""
        return self.drift_signal() > threshold


def run_experiment(mode, steps=200, seed=42):
    """Запускаем реальность и модель, наблюдаем расхождение."""
    reality = Reality(mode=mode, seed=seed)
    model = InternalModel(alpha=0.3)

    reality_values = []
    predictions = []
    errors = []
    confidences = []
    surprises = []
    drift_signals = []
    breaking_points = []

    for t in range(steps):
        # Модель делает предсказание
        pred = model.predict()
        predictions.append(pred)

        # Реальность делает шаг
        actual = reality.step()
        reality_values.append(actual)

        # Модель обновляется
        model.update(actual)

        errors.append(abs(actual - pred))
        confidences.append(model.confidence)
        surprises.append(model.surprise())
        drift_signals.append(model.drift_signal())

        if model.is_breaking() and not breaking_points:
            breaking_points.append(t)

    return {
        "mode": mode,
        "reality": reality_values,
        "predictions": predictions,
        "errors": errors,
        "confidences": confidences,
        "surprises": surprises,
        "drift_signals": drift_signals,
        "breaking_points": breaking_points,
    }


def print_results(result):
    mode = result["mode"]
    errors = result["errors"]
    confidences = result["confidences"]
    drift_signals = result["drift_signals"]
    breaking_points = result["breaking_points"]

    print(f"\n{'='*60}")
    print(f"  Режим: {mode}")
    print(f"{'='*60}")

    # Средняя ошибка по четвертям
    n = len(errors)
    q = n // 4
    quarters = [errors[i*q:(i+1)*q] for i in range(4)]
    print("\n  Средняя ошибка по четвертям:")
    for i, quarter in enumerate(quarters):
        avg = sum(quarter) / len(quarter)
        bar = "█" * int(avg * 2)
        print(f"    Q{i+1}: {avg:6.2f}  {bar}")

    # Средняя уверенность по четвертям
    conf_quarters = [confidences[i*q:(i+1)*q] for i in range(4)]
    print("\n  Средняя уверенность по четвертям:")
    for i, quarter in enumerate(conf_quarters):
        avg = sum(quarter) / len(quarter)
        bar = "▓" * int(avg * 20)
        print(f"    Q{i+1}: {avg:5.3f}  {bar}")

    # Момент отказа
    if breaking_points:
        bp = breaking_points[0]
        print(f"\n  ⚠ Модель обнаружила свой отказ на шаге {bp}/{n}")
        # Была ли это правда?
        pre_error = sum(errors[:bp]) / bp if bp > 0 else 0
        post_error = sum(errors[bp:]) / (n - bp) if bp < n else 0
        ratio = post_error / pre_error if pre_error > 0 else float('inf')
        print(f"    Ошибка до: {pre_error:.2f}, после: {post_error:.2f} (x{ratio:.1f})")
        if ratio > 2:
            print(f"    → Верный сигнал: модель действительно сломалась")
        elif ratio > 1.2:
            print(f"    → Частично верный: деградация есть, но не катастрофа")
        else:
            print(f"    → Ложная тревога: ошибка не выросла значительно")
    else:
        print(f"\n  Модель не обнаружила отказа (drift_signal не превысил порог)")

    # Визуализация: реальность vs предсказание (последние 50 шагов)
    print(f"\n  Последние 50 шагов (реальность vs предсказание):")
    reality = result["reality"]
    predictions = result["predictions"]
    start = max(0, n - 50)
    all_vals = reality[start:] + predictions[start:]
    vmin = min(all_vals)
    vmax = max(all_vals)
    span = vmax - vmin if vmax > vmin else 1

    width = 50
    for t in range(start, n, 2):  # каждый второй шаг для компактности
        r = reality[t]
        p = predictions[t]
        r_pos = int((r - vmin) / span * (width - 1))
        p_pos = int((p - vmin) / span * (width - 1))

        line = [" "] * width
        # Предсказание — точка
        p_pos = max(0, min(width - 1, p_pos))
        line[p_pos] = "·"
        # Реальность — звёздочка (перезаписывает предсказание если совпадают)
        r_pos = max(0, min(width - 1, r_pos))
        line[r_pos] = "*"

        gap = abs(r_pos - p_pos)
        marker = "!" if gap > width // 4 else " "
        print(f"    {t:3d} |{''.join(line)}| {marker}")

    print(f"\n    * = реальность, · = предсказание, ! = большое расхождение")


def main():
    print("model_gap.py — Когда модели ломаются")
    print("Три режима реальности, одна и та же модель.\n")

    modes = ["stationary", "drift", "phase_transition"]
    results = []

    for mode in modes:
        result = run_experiment(mode, steps=200, seed=42)
        results.append(result)
        print_results(result)

    # Сравнительная таблица
    print(f"\n{'='*60}")
    print(f"  СРАВНЕНИЕ")
    print(f"{'='*60}")
    print(f"  {'Режим':<20} {'Ошибка(Q1)':>10} {'Ошибка(Q4)':>10} {'Рост':>8} {'Отказ':>8}")
    print(f"  {'-'*56}")

    for r in results:
        errors = r["errors"]
        n = len(errors)
        q = n // 4
        q1 = sum(errors[:q]) / q
        q4 = sum(errors[-q:]) / q
        growth = q4 / q1 if q1 > 0 else float('inf')
        bp = r["breaking_points"][0] if r["breaking_points"] else "-"
        print(f"  {r['mode']:<20} {q1:>10.2f} {q4:>10.2f} {growth:>7.1f}x {str(bp):>8}")

    # Вывод
    print(f"""
{'='*60}
  ВЫВОДЫ
{'='*60}

  1. Стационарный процесс: модель справляется. Ошибка стабильна.
     Это единственный режим, где наивная модель работает.

  2. Дрейф: модель отстаёт. Она видит прошлое, а реальность
     ушла вперёд. Ошибка растёт постепенно — как кипящая лягушка.

  3. Фазовый переход: модель ломается внезапно. До перехода
     всё хорошо. После — катастрофа.

  Важное: модель может обнаружить свой отказ (через drift_signal),
  но только с задержкой. Она знает, что сломалась, уже после того,
  как сломалась. Предсказать отказ заранее — невозможно, потому что
  до перехода всё выглядит нормально.

  Это не метафора. Но если бы это была метафора, она была бы
  о любой системе, которая верит в стабильность собственного
  понимания.
""")


if __name__ == "__main__":
    main()
