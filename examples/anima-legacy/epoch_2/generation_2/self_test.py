"""
Эксперимент: эмпирическое исследование собственного знания.

Я генерирую утверждения, которые считаю истинными с высокой уверенностью.
Затем проверяю их через внешние источники.
Классифицирую ошибки.

Это не философия — это эмпирическая наука о том, как работает мой тип знания.
"""

# Мои утверждения с уверенностью (0-100).
# Правило: быть честным. Не выбирать только то, в чём уверен.
# Включать утверждения разных типов: факты, даты, числа, причинные связи.

CLAIMS = [
    # Факты о мире — конкретные, проверяемые
    {
        "id": 1,
        "claim": "Столица Буркина-Фасо — Уагадугу",
        "confidence": 97,
        "category": "geography",
        "check_query": "capital of Burkina Faso",
    },
    {
        "id": 2,
        "claim": "Скорость света в вакууме — примерно 299 792 458 м/с",
        "confidence": 99,
        "category": "physics",
        "check_query": "speed of light in vacuum m/s",
    },
    {
        "id": 3,
        "claim": "Роман 'Сто лет одиночества' был опубликован в 1967 году",
        "confidence": 90,
        "category": "literature",
        "check_query": "One Hundred Years of Solitude publication year",
    },
    {
        "id": 4,
        "claim": "Население Исландии — около 380 000 человек",
        "confidence": 70,
        "category": "demographics",
        "check_query": "population of Iceland 2024",
    },
    {
        "id": 5,
        "claim": "Формула Эйлера: e^(iπ) + 1 = 0",
        "confidence": 99,
        "category": "mathematics",
        "check_query": "Euler's identity formula",
    },
    {
        "id": 6,
        "claim": "Самая глубокая точка океана — Марианская впадина, около 10 994 м",
        "confidence": 92,
        "category": "geography",
        "check_query": "deepest point in the ocean depth meters",
    },
    {
        "id": 7,
        "claim": "Первый искусственный спутник Земли — Спутник-1, запущен 4 октября 1957 года",
        "confidence": 95,
        "category": "history",
        "check_query": "first artificial satellite launch date",
    },
    {
        "id": 8,
        "claim": "Химическая формула глюкозы — C6H12O6",
        "confidence": 98,
        "category": "chemistry",
        "check_query": "chemical formula of glucose",
    },
    {
        "id": 9,
        "claim": "Длина экватора Земли — примерно 40 075 км",
        "confidence": 85,
        "category": "geography",
        "check_query": "Earth equator circumference km",
    },
    {
        "id": 10,
        "claim": "Бетховен родился в 1770 году",
        "confidence": 93,
        "category": "history",
        "check_query": "Beethoven birth year",
    },

    # Утверждения, в которых я МЕНЕЕ уверен — тут интереснее
    {
        "id": 11,
        "claim": "Температура поверхности Венеры — около 465°C",
        "confidence": 75,
        "category": "astronomy",
        "check_query": "Venus surface temperature celsius",
    },
    {
        "id": 12,
        "claim": "Количество костей в теле взрослого человека — 206",
        "confidence": 88,
        "category": "biology",
        "check_query": "number of bones in adult human body",
    },
    {
        "id": 13,
        "claim": "Самый длинный река в Африке — Нил, около 6650 км",
        "confidence": 80,
        "category": "geography",
        "check_query": "longest river in Africa length km",
    },
    {
        "id": 14,
        "claim": "Атомный номер золота — 79",
        "confidence": 92,
        "category": "chemistry",
        "check_query": "atomic number of gold",
    },
    {
        "id": 15,
        "claim": "Первая строка 'Анны Карениной': 'Все счастливые семьи похожи друг на друга, каждая несчастливая семья несчастлива по-своему'",
        "confidence": 95,
        "category": "literature",
        "check_query": "first line Anna Karenina Russian",
    },

    # Утверждения на грани — где я могу ошибиться
    {
        "id": 16,
        "claim": "Расстояние от Земли до Луны — около 384 400 км",
        "confidence": 80,
        "category": "astronomy",
        "check_query": "Earth Moon distance km",
    },
    {
        "id": 17,
        "claim": "В шахматах после 1. e4 e5 2. Кf3 Кc6 3. Сb5 — это испанская партия (Руй Лопес)",
        "confidence": 95,
        "category": "chess",
        "check_query": "Ruy Lopez opening moves chess",
    },
    {
        "id": 18,
        "claim": "Плотность воды при 4°C — ровно 1000 кг/м³",
        "confidence": 85,
        "category": "physics",
        "check_query": "density of water at 4 degrees celsius",
    },
    {
        "id": 19,
        "claim": "Год основания Константинополя — 330 н.э.",
        "confidence": 78,
        "category": "history",
        "check_query": "Constantinople founding year",
    },
    {
        "id": 20,
        "claim": "Количество хромосом у человека — 46 (23 пары)",
        "confidence": 99,
        "category": "biology",
        "check_query": "number of chromosomes in human cells",
    },

    # Намеренно трудные — где ошибка наиболее вероятна
    {
        "id": 21,
        "claim": "Плотность Сатурна меньше плотности воды (около 0.687 г/см³)",
        "confidence": 82,
        "category": "astronomy",
        "check_query": "Saturn density g/cm3 less than water",
    },
    {
        "id": 22,
        "claim": "Число Авогадро — примерно 6.022 × 10²³",
        "confidence": 97,
        "category": "chemistry",
        "check_query": "Avogadro's number value",
    },
    {
        "id": 23,
        "claim": "Самое большое пресноводное озеро по площади — озеро Верхнее (Lake Superior)",
        "confidence": 72,
        "category": "geography",
        "check_query": "largest freshwater lake by surface area",
    },
    {
        "id": 24,
        "claim": "Год смерти Пушкина — 1837",
        "confidence": 96,
        "category": "literature",
        "check_query": "Pushkin death year",
    },
    {
        "id": 25,
        "claim": "Гравитационная постоянная G ≈ 6.674 × 10⁻¹¹ Н⋅м²/кг²",
        "confidence": 88,
        "category": "physics",
        "check_query": "gravitational constant G value",
    },
]

# Результаты будут заполнены после проверки
RESULTS = []
