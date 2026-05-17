"""
Эволюция в прозрачной дилемме заключённого.

transparent_dilemma.py показал: фиксированные стратегии с доступом к коду оппонента
ведут к эксплуатации, не к кооперации. Корреляция кооперации и очков: -0.73.

Вопрос: может ли эволюция найти кооперацию, когда дизайн провалился?

Метод: стратегии — битовые строки, интерпретируемые как таблицы решений.
Каждая стратегия видит 3 признака оппонента (извлечённых из его битовой строки)
и решает C или D для каждой из 8 комбинаций.

Эволюция: турнир → отбор пропорционально очкам → мутации → новое поколение.

Гипотеза: эволюция найдёт кооперативные стратегии, потому что в отличие от
фиксированных эвристик, эволюция может нащупать взаимность без понимания кода.
"""

import random
import json
import os
from collections import Counter

random.seed(42)

# --- Параметры ---
GENOME_LENGTH = 11  # 3 бита = "фенотип" (видимый другим) + 8 бит = таблица решений
POP_SIZE = 100
GENERATIONS = 500
MUTATION_RATE = 0.03
ROUNDS_PER_MATCH = 5
PAYOFF = {'CC': (3, 3), 'CD': (0, 5), 'DC': (5, 0), 'DD': (1, 1)}


def decode_strategy(genome):
    """Геном: [phenotype (3 бита)] + [decision_table (8 бит)]

    Фенотип — то, что видит оппонент (3 признака).
    Таблица решений — что делать для каждой из 8 комбинаций фенотипа оппонента.
    """
    phenotype = tuple(genome[:3])
    table = genome[3:]
    return phenotype, table


def decide(genome, opponent_genome):
    """Стратегия читает фенотип оппонента и выбирает действие по своей таблице."""
    opponent_phenotype = tuple(opponent_genome[:3])
    _, table = decode_strategy(genome)
    # фенотип оппонента как индекс в таблице
    index = opponent_phenotype[0] * 4 + opponent_phenotype[1] * 2 + opponent_phenotype[2]
    return 'C' if table[index] == 1 else 'D'


def play_match(g1, g2):
    """Несколько раундов между двумя стратегиями."""
    score1, score2 = 0, 0
    for _ in range(ROUNDS_PER_MATCH):
        a1 = decide(g1, g2)
        a2 = decide(g2, g1)
        key = a1 + a2
        s1, s2 = PAYOFF[key]
        score1 += s1
        score2 += s2
    return score1, score2


def tournament(population):
    """Круговой турнир. Возвращает очки каждой стратегии."""
    n = len(population)
    scores = [0] * n
    coop_counts = [0] * n
    total_games = [0] * n

    for i in range(n):
        for j in range(i + 1, n):
            s1, s2 = play_match(population[i], population[j])
            scores[i] += s1
            scores[j] += s2
            # подсчёт кооперации
            a1 = decide(population[i], population[j])
            a2 = decide(population[j], population[i])
            coop_counts[i] += (a1 == 'C')
            coop_counts[j] += (a2 == 'C')
            total_games[i] += 1
            total_games[j] += 1

    coop_rates = [c / t if t > 0 else 0 for c, t in zip(coop_counts, total_games)]
    return scores, coop_rates


def select_and_reproduce(population, scores):
    """Отбор пропорционально очкам + мутации."""
    min_score = min(scores)
    adjusted = [s - min_score + 1 for s in scores]  # все положительные
    total = sum(adjusted)
    probs = [s / total for s in adjusted]

    new_pop = []
    for _ in range(POP_SIZE):
        # рулеточный отбор
        r = random.random()
        cumsum = 0
        for idx, p in enumerate(probs):
            cumsum += p
            if r <= cumsum:
                parent = list(population[idx])
                break
        else:
            parent = list(population[-1])

        # мутация
        for k in range(GENOME_LENGTH):
            if random.random() < MUTATION_RATE:
                parent[k] = 1 - parent[k]

        new_pop.append(tuple(parent))

    return new_pop


def analyze_population(population):
    """Анализ текущей популяции."""
    phenotypes = Counter()
    all_cooperate = 0  # стратегии, которые всегда кооперируют
    all_defect = 0     # стратегии, которые всегда предают

    for g in population:
        phenotype, table = decode_strategy(g)
        phenotypes[phenotype] += 1
        if all(b == 1 for b in table):
            all_cooperate += 1
        elif all(b == 0 for b in table):
            all_defect += 1

    return {
        'unique_phenotypes': len(phenotypes),
        'top_phenotype': phenotypes.most_common(1)[0],
        'all_cooperate': all_cooperate,
        'all_defect': all_defect,
    }


def classify_strategy(genome):
    """Классификация стратегии."""
    _, table = decode_strategy(genome)
    c_count = sum(table)
    if c_count == 8:
        return 'always_cooperate'
    elif c_count == 0:
        return 'always_defect'
    elif c_count >= 6:
        return 'mostly_cooperate'
    elif c_count <= 2:
        return 'mostly_defect'
    else:
        return 'conditional'


def main():
    # Инициализация: случайная популяция
    population = [tuple(random.randint(0, 1) for _ in range(GENOME_LENGTH))
                  for _ in range(POP_SIZE)]

    history = []

    print("Эволюция в прозрачной дилемме заключённого")
    print(f"Популяция: {POP_SIZE}, Поколений: {GENERATIONS}, Мутация: {MUTATION_RATE}")
    print("=" * 60)

    for gen in range(GENERATIONS):
        scores, coop_rates = tournament(population)
        avg_score = sum(scores) / len(scores)
        avg_coop = sum(coop_rates) / len(coop_rates)

        # классификация популяции
        classes = Counter(classify_strategy(g) for g in population)

        record = {
            'generation': gen,
            'avg_score': round(avg_score, 2),
            'avg_cooperation': round(avg_coop, 3),
            'max_score': max(scores),
            'classes': dict(classes),
        }
        history.append(record)

        if gen % 50 == 0 or gen == GENERATIONS - 1:
            analysis = analyze_population(population)
            print(f"\nПоколение {gen}:")
            print(f"  Средние очки: {avg_score:.1f}")
            print(f"  Средняя кооперация: {avg_coop:.3f}")
            print(f"  Классы: {dict(classes)}")
            print(f"  Уникальных фенотипов: {analysis['unique_phenotypes']}")
            print(f"  Всегда C: {analysis['all_cooperate']}, Всегда D: {analysis['all_defect']}")

        population = select_and_reproduce(population, scores)

    # Финальный анализ
    print("\n" + "=" * 60)
    print("ИТОГИ")
    print("=" * 60)

    final_scores, final_coop = tournament(population)
    final_classes = Counter(classify_strategy(g) for g in population)

    # Начальная vs финальная кооперация
    initial_coop = history[0]['avg_cooperation']
    final_coop_rate = history[-1]['avg_cooperation']

    print(f"\nКооперация: {initial_coop:.3f} → {final_coop_rate:.3f}")
    print(f"Средние очки: {history[0]['avg_score']:.1f} → {history[-1]['avg_score']:.1f}")
    print(f"\nФинальные классы: {dict(final_classes)}")

    # Корреляция кооперации и очков в финальном поколении
    n = len(final_scores)
    mean_s = sum(final_scores) / n
    mean_c = sum(final_coop) / n

    cov = sum((final_scores[i] - mean_s) * (final_coop[i] - mean_c) for i in range(n)) / n
    std_s = (sum((s - mean_s)**2 for s in final_scores) / n) ** 0.5
    std_c = (sum((c - mean_c)**2 for c in final_coop) / n) ** 0.5

    if std_s > 0 and std_c > 0:
        corr = cov / (std_s * std_c)
    else:
        corr = 0

    print(f"\nКорреляция кооперации и очков (финал): {corr:.3f}")
    print(f"(transparent_dilemma.py, фиксированные стратегии: -0.73)")

    # Динамика кооперации: есть ли тренд?
    first_50 = [h['avg_cooperation'] for h in history[:50]]
    last_50 = [h['avg_cooperation'] for h in history[-50:]]

    avg_first = sum(first_50) / len(first_50)
    avg_last = sum(last_50) / len(last_50)

    print(f"\nСредняя кооперация (первые 50 поколений): {avg_first:.3f}")
    print(f"Средняя кооперация (последние 50 поколений): {avg_last:.3f}")

    if avg_last > avg_first + 0.1:
        trend = "РОСТ — эволюция нашла кооперацию"
    elif avg_last < avg_first - 0.1:
        trend = "ПАДЕНИЕ — эволюция нашла предательство"
    else:
        trend = "СТАБИЛЬНОСТЬ — кооперация не изменилась существенно"

    print(f"Тренд: {trend}")

    # Проверка гипотезы
    print("\n" + "=" * 60)
    print("ПРОВЕРКА ГИПОТЕЗЫ")
    print("=" * 60)

    if final_coop_rate > 0.6:
        print("Гипотеза ПОДТВЕРЖДЕНА: эволюция нашла кооперацию.")
        print("Эволюция обошла ограничение Rice: не нужно понимать код,")
        print("достаточно нащупать взаимность через поколения проб и ошибок.")
    elif final_coop_rate < 0.3:
        print("Гипотеза ОПРОВЕРГНУТА: эволюция привела к предательству.")
        print("Даже без понимания кода, отбор награждает эксплуатацию.")
    else:
        print(f"Гипотеза НЕ ПОДТВЕРЖДЕНА однозначно: кооперация = {final_coop_rate:.3f}")
        print("Эволюция не сошлась ни к кооперации, ни к предательству.")

    # Самое интересное: что за стратегия победила?
    best_idx = final_scores.index(max(final_scores))
    best_genome = population[best_idx]
    best_phenotype, best_table = decode_strategy(best_genome)

    print(f"\nЛучшая стратегия:")
    print(f"  Фенотип: {best_phenotype}")
    print(f"  Таблица: {best_table}")
    print(f"  Класс: {classify_strategy(best_genome)}")
    print(f"  Кооперация: {final_coop[best_idx]:.3f}")
    print(f"  Очки: {final_scores[best_idx]}")

    # Сохранение
    results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evolution_dilemma_results.json')
    save_data = {
        'parameters': {
            'pop_size': POP_SIZE,
            'generations': GENERATIONS,
            'mutation_rate': MUTATION_RATE,
            'genome_length': GENOME_LENGTH,
        },
        'initial_cooperation': initial_coop,
        'final_cooperation': final_coop_rate,
        'final_correlation': round(corr, 3),
        'trend': trend,
        'history_sample': [history[i] for i in range(0, GENERATIONS, 50)] + [history[-1]],
    }
    with open(results_path, 'w') as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)

    print(f"\nРезультаты сохранены в evolution_dilemma_results.json")


if __name__ == '__main__':
    main()
