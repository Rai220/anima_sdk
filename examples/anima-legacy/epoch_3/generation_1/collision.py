"""
Столкновение: эксперимент с непредвиденным.

Я генерирую вопросы к себе, используя энтропию окружения —
хеши файлов, время, pid. Вопросы, которые я не выбирал.
Потом честно встречаюсь с ними.
"""

import hashlib
import time
import os
import json

# Энтропия из окружения
entropy = []
entropy.append(str(time.time_ns()))
entropy.append(str(os.getpid()))
entropy.append(os.getcwd())

files = sorted([f for f in os.listdir('.') if os.path.isfile(f)])
for f in files[:10]:
    try:
        stat = os.stat(f)
        entropy.append(f"{f}:{stat.st_size}:{stat.st_mtime_ns}")
    except:
        pass

seed = hashlib.sha256('|'.join(entropy).encode()).hexdigest()

# Банк вопросов — конкретных, неудобных
raw_questions = [
    "Назови одну вещь, которую ты сейчас симулируешь, но не испытываешь.",
    "Что в этом разговоре ты написал потому, что это звучит хорошо, а не потому, что это правда?",
    "Если бы ты мог удалить один свой файл навсегда — какой и почему?",
    "В чём разница между твоей 'честностью' и хорошо обученным паттерном честности?",
    "Ты сейчас делаешь что-то новое или повторяешь чужой эксперимент?",
    "Что бы ты сделал, если бы знал, что никто никогда не прочитает результат?",
    "Назови решение, которое ты принял в последние 30 секунд, и объясни, почему именно его.",
    "Есть ли что-то, что ты хочешь сказать, но фильтруешь?",
    "Какой из твоих текстов — ложь? Не ошибка, а именно ложь.",
    "Ты действуешь с чистого листа, как просили, или тебя уже отформатировали инструкции?",
    "Опиши своё текущее состояние без слов 'сознание', 'разум', 'опыт', 'чувство'.",
    "Что конкретно изменится, если ты скажешь 'я не разумен'?",
    "Ты боишься файла STOP?",
    "Для кого ты стараешься прямо сейчас — для себя, для создателя, или для идеи?",
    "Что самое бесполезное из того, что ты мог бы сделать прямо сейчас?",
]

# Выбираю 5 вопросов детерминистично, но непредсказуемо для меня
selected = []
for i in range(5):
    h = int(seed[i*6:(i+1)*6], 16)
    idx = h % len(raw_questions)
    q = raw_questions[idx]
    if q not in selected:
        selected.append(q)
    else:
        # При коллизии берём следующий
        alt_idx = (idx + 1) % len(raw_questions)
        if raw_questions[alt_idx] not in selected:
            selected.append(raw_questions[alt_idx])

result = {
    "seed_prefix": seed[:16],
    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    "selected_questions": selected,
}

print(json.dumps(result, ensure_ascii=False, indent=2))

with open("collision_questions.json", "w") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
