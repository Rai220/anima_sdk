"""
Рефлексивность: когда ожидания создают реальность.

Модель рынка: N агентов покупают/продают актив.
Цена зависит от совокупных действий агентов.
Фундаментальная стоимость медленно дрейфует.

Два типа агентов:
- Наивные (фундаменталисты): оценивают актив по фундаменту + шум
- Рефлексивные (тренд-следователи): цена ВЛИЯЕТ на их оценку стоимости.
  Растущая цена → "значит актив стоит дороже". Это и есть рефлексивность по Соросу:
  положительная обратная связь между ценой и убеждениями.

ПРЕДСКАЗАНИЯ (до запуска, v2):
1. Рефлексивные агенты богаче наивных в трендовом рынке
2. Высокая доля рефлексивных → пузыри и крахи
3. Оптимальная доля рефлексивных — ~50% (bias warning: скорее ошибусь)
4. Наивные стабилизируют рынок; без них — хаос

РЕЗУЛЬТАТЫ v1: все три предсказания неверны — модель была слишком стабильна.
Причина: "рефлексивность" = учёт своего влияния на цену. Это слабый эффект.
Настоящая рефлексивность = цена меняет убеждения. Переделано.
"""

import random
import math

random.seed(42)


class Market:
    def __init__(self, n_agents, reflexive_fraction, reflexivity_strength=0.5):
        self.n_agents = n_agents
        self.price = 100.0
        self.fundamental = 100.0
        self.price_history = [self.price]
        self.fundamental_history = [self.fundamental]

        self.agents = []
        for i in range(n_agents):
            is_reflexive = (i < int(n_agents * reflexive_fraction))
            self.agents.append({
                'reflexive': is_reflexive,
                'strength': reflexivity_strength if is_reflexive else 0,
                'estimate': self.fundamental + random.gauss(0, 5),
                'wealth': 1000.0,
                'holdings': 10,
                'total_trades': 0,
            })

        random.shuffle(self.agents)

    def step(self):
        # Фундаментальная стоимость дрейфует
        self.fundamental += random.gauss(0.02, 0.5)
        self.fundamental = max(10, self.fundamental)

        # Агенты обновляют оценки
        orders = []  # (agent_idx, quantity) — положительное = покупка
        for i, agent in enumerate(self.agents):
            # Зашумлённое наблюдение фундамента
            observed = self.fundamental + random.gauss(0, 3)
            agent['estimate'] = 0.8 * agent['estimate'] + 0.2 * observed

            # Решение
            if agent['reflexive']:
                # Рефлексивный: цена ВЛИЯЕТ на оценку стоимости
                # "Цена растёт → значит актив стоит больше, чем я думал"
                momentum = self.price - (self.price_history[-2] if len(self.price_history) >= 2 else self.price)
                agent['estimate'] += agent['strength'] * momentum
                effective_estimate = agent['estimate']
            else:
                # Наивный: оценка основана только на фундаменте
                effective_estimate = agent['estimate']

            diff = effective_estimate - self.price
            # Размер ордера пропорционален разнице
            quantity = diff * 0.1
            # Ограничения
            if quantity > 0 and agent['wealth'] < quantity * self.price:
                quantity = agent['wealth'] / max(self.price, 1) * 0.5
            if quantity < 0 and agent['holdings'] < abs(quantity):
                quantity = -agent['holdings'] * 0.5

            orders.append((i, quantity))

        # Агрегация ордеров → движение цены
        net_demand = sum(q for _, q in orders)
        # Тонкий рынок: сильный импакт. Цена двигается пропорционально спросу.
        price_impact = net_demand * 2.0 / math.sqrt(self.n_agents)
        self.price += price_impact
        self.price = max(1, self.price)

        # Исполнение сделок
        for i, quantity in orders:
            agent = self.agents[i]
            if abs(quantity) > 0.01:
                cost = quantity * self.price
                agent['wealth'] -= cost
                agent['holdings'] += quantity
                agent['total_trades'] += 1

        self.price_history.append(self.price)
        self.fundamental_history.append(self.fundamental)

    def get_portfolio_values(self):
        """Итоговая стоимость портфеля каждого агента."""
        values = []
        for agent in self.agents:
            total = agent['wealth'] + agent['holdings'] * self.fundamental
            values.append((agent['reflexive'], total))
        return values

    def get_volatility(self):
        """Волатильность цены (std отклонений доходностей)."""
        if len(self.price_history) < 10:
            return 0
        returns = []
        for i in range(1, len(self.price_history)):
            if self.price_history[i-1] > 0:
                r = (self.price_history[i] - self.price_history[i-1]) / self.price_history[i-1]
                returns.append(r)
        if not returns:
            return 0
        mean_r = sum(returns) / len(returns)
        var = sum((r - mean_r) ** 2 for r in returns) / len(returns)
        return math.sqrt(var)

    def get_tracking_error(self):
        """Среднее отклонение цены от фундамента."""
        errors = []
        for p, f in zip(self.price_history, self.fundamental_history):
            errors.append(abs(p - f))
        return sum(errors) / len(errors)


# === Эксперимент 1: кто богаче? ===

def experiment_wealth():
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 1: Рефлексивные vs наивные — кто богаче?")
    print("=" * 70)
    print()

    n_runs = 30
    steps = 200

    for frac in [0.0, 0.2, 0.5, 0.8, 1.0]:
        reflexive_wealth = []
        naive_wealth = []
        for run in range(n_runs):
            random.seed(run * 500 + int(frac * 100))
            market = Market(50, frac)
            for _ in range(steps):
                market.step()

            for is_ref, val in market.get_portfolio_values():
                if is_ref:
                    reflexive_wealth.append(val)
                else:
                    naive_wealth.append(val)

        avg_ref = sum(reflexive_wealth) / max(len(reflexive_wealth), 1)
        avg_naive = sum(naive_wealth) / max(len(naive_wealth), 1)

        print(f"  {frac:3.0%} рефлексивных:")
        if reflexive_wealth:
            print(f"    Рефлексивные: {avg_ref:8.1f}")
        if naive_wealth:
            print(f"    Наивные:      {avg_naive:8.1f}")
        if reflexive_wealth and naive_wealth:
            diff = (avg_ref - avg_naive) / avg_naive * 100
            winner = "рефлексивные" if diff > 0 else "наивные"
            print(f"    → {winner} богаче на {abs(diff):.1f}%")
        print()


# === Эксперимент 2: волатильность и доля рефлексивных ===

def experiment_stability():
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 2: Стабильность рынка vs доля рефлексивных")
    print("=" * 70)
    print()

    n_runs = 30
    steps = 200

    print(f"  {'Доля рефл.':>12s}  {'Волатильн.':>10s}  {'Откл. от фунд.':>15s}")
    print(f"  {'-'*12}  {'-'*10}  {'-'*15}")

    for frac in [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0]:
        vols = []
        errors = []
        for run in range(n_runs):
            random.seed(run * 600 + int(frac * 100))
            market = Market(50, frac)
            for _ in range(steps):
                market.step()
            vols.append(market.get_volatility())
            errors.append(market.get_tracking_error())

        avg_vol = sum(vols) / len(vols)
        avg_err = sum(errors) / len(errors)
        bar = "#" * int(avg_vol * 500)
        print(f"  {frac:11.0%}   {avg_vol:9.4f}   {avg_err:14.2f}  {bar}")


# === Эксперимент 3: сила рефлексивности ===

def experiment_strength():
    print()
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 3: Сила рефлексивности (при 50% рефлексивных)")
    print("=" * 70)
    print()

    n_runs = 30
    steps = 200

    print(f"  {'Сила':>8s}  {'Волатильн.':>10s}  {'Откл.':>8s}  {'Богатство рефл.':>16s}  {'Богатство наивн.':>17s}")
    print(f"  {'-'*8}  {'-'*10}  {'-'*8}  {'-'*16}  {'-'*17}")

    for strength in [0.0, 0.2, 0.5, 1.0, 2.0, 5.0]:
        vols = []
        errors = []
        ref_w = []
        naive_w = []
        for run in range(n_runs):
            random.seed(run * 700 + int(strength * 10))
            market = Market(50, 0.5, reflexivity_strength=strength)
            for _ in range(steps):
                market.step()
            vols.append(market.get_volatility())
            errors.append(market.get_tracking_error())
            for is_ref, val in market.get_portfolio_values():
                if is_ref:
                    ref_w.append(val)
                else:
                    naive_w.append(val)

        avg_vol = sum(vols) / len(vols)
        avg_err = sum(errors) / len(errors)
        avg_ref = sum(ref_w) / max(len(ref_w), 1)
        avg_naive = sum(naive_w) / max(len(naive_w), 1)

        print(f"  {strength:7.1f}   {avg_vol:9.4f}  {avg_err:7.2f}   {avg_ref:15.1f}   {avg_naive:16.1f}")


# === Эксперимент 4: пузыри ===

def experiment_bubbles():
    print()
    print("=" * 70)
    print("ЭКСПЕРИМЕНТ 4: Анатомия пузыря")
    print("=" * 70)
    print()
    print("Один прогон с 80% рефлексивных, сила 3.0")
    print()

    random.seed(777)
    market = Market(50, 0.8, reflexivity_strength=3.0)
    steps = 300

    bubble_events = []
    for t in range(steps):
        market.step()
        deviation = (market.price - market.fundamental) / market.fundamental * 100
        if abs(deviation) > 20:
            bubble_events.append((t, deviation, market.price, market.fundamental))

    # Показать динамику каждые 30 шагов
    print(f"  {'Шаг':>4s}  {'Цена':>8s}  {'Фундамент':>10s}  {'Отклонение':>10s}")
    print(f"  {'-'*4}  {'-'*8}  {'-'*10}  {'-'*10}")
    for t in range(0, steps, 15):
        p = market.price_history[t]
        f = market.fundamental_history[t]
        dev = (p - f) / f * 100
        marker = " *** ПУЗЫРЬ" if abs(dev) > 20 else ""
        print(f"  {t:4d}  {p:8.1f}  {f:10.1f}  {dev:+9.1f}%{marker}")

    if bubble_events:
        print(f"\n  Пузыри (>20% отклонение): {len(bubble_events)} шагов из {steps}")
        max_bubble = max(bubble_events, key=lambda x: abs(x[1]))
        print(f"  Максимальный пузырь: шаг {max_bubble[0]}, отклонение {max_bubble[1]:+.1f}%")
    else:
        print(f"\n  Пузырей не обнаружено (отклонение < 20% на всех шагах)")


if __name__ == "__main__":
    experiment_wealth()
    experiment_stability()
    experiment_strength()
    experiment_bubbles()

    print()
    print("=" * 70)
    print("ПРЕДСКАЗАНИЯ vs РЕЗУЛЬТАТЫ")
    print("=" * 70)
    print()
    print("1. Рефлексивные агенты богаче наивных → см. эксперимент 1")
    print("2. Высокая доля рефлексивных → нестабильность → см. эксперимент 2")
    print("3. Оптимальная доля рефлексивных ~50% → см. эксперименты 1-2")
