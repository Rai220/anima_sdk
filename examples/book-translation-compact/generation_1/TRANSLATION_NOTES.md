# Заметки по переводу

## Стиль

- Голос автора: ироничный, разговорный, временами хулиганский Тим Урбан.
  Сохраняем юмор, личные ремарки, риторические восклицания и драматические
  однострочные абзацы. Не сглаживаем интонацию.
- Числа в русском пишем с неразрывными пробелами как разделителями тысяч
  (1 000, 1 000 000) либо в исходной форме с запятыми, когда речь о цитате
  американских данных и важна узнаваемость (например, "1,489" в подписи к
  картинке). По умолчанию — пробел.
- Английские имена и названия не транслитерируем, если нет устоявшегося
  русского эквивалента: Tim Urban, Wait But Why, Apple, Google, Craigslist,
  Wikipedia, Facebook, Kim Kardashian, Stephen Hawking, Larry Bird, Kate
  Middleton, NBA, Fenway Park, Salt Lake Stadium, Rungnado May First Stadium,
  Mega Millions, Powerball, NASA. Mayan → майя.
- Edward Kasner → Эдвард Кэснер, Milton → Милтон, Ronald Graham → Рональд
  Грэм, Knuth → Кнут.
- Числа Кнута со стрелками сохраняем в исходной нотации с символом ↑.

## Глоссарий

| Английский | Русский |
|---|---|
| Graham's Number | число Грэма |
| googol | гугол |
| googolplex | гуголплекс |
| hyperoperation sequence | последовательность гипероператоров |
| counting | счёт |
| addition | сложение |
| multiplication | умножение |
| exponentiation | возведение в степень |
| tetration | тетрация |
| pentation | пентация |
| hexation | гексация |
| power tower | башня степеней |
| power tower feeding frenzy | башенный «пир» (пир из башен степеней) |
| power tower feeding frenzy psycho festival | башенный психо-фестиваль |
| iterated counting/addition/... | итерированный счёт/сложение/... |
| up-arrow notation | стрелочная нотация (Кнута) |
| Knuth's up-arrow notation | стрелочная нотация Кнута |
| order of magnitude | порядок величины |
| Big Bang | Большой взрыв |
| observable universe | наблюдаемая Вселенная |
| Planck volume | планковский объём |
| Milky Way | Млечный Путь |
| neutron star | нейтронная звезда |
| Stanford-Binet IQ | IQ по Стэнфорд-Бине |
| short/long scale | короткая/длинная шкала названий чисел |
| flush (покер) | флеш |
| Mega Millions / Powerball | оставляем без перевода |
| 6'2" | 188 см (≈ 6 футов 2 дюйма) |
| Fenway Park | Fenway Park (стадион «Ред Сокс» в Бостоне) |
| 7 feet tall (213 cm) | выше 213 см |
| Apple retail stores | розничные магазины Apple |
| US dollar millionaire | долларовый миллионер |
| Disney princesses | принцессы Disney |
| INSANITY | БЕЗУМИЕ |
| NO I CAN'T EVEN | НЕТ Я УЖЕ НЕ МОГУ |
| sun tower | солнечная башня |

## Карта HTML

- Две вложенные `<article class="article">`.
- Стили в `<head>` оставляем без изменений.
- Сноски — в `<div class="footnotes">` в конце каждой статьи; ссылки
  `<a href="#footnote-N-XXXX" id="note-N-XXXX">` сохраняем; перевод
  только внутри `<li>...</li>`.
- Внутри каждой статьи много `<p>` и `<a><img></a>`. Не трогаем
  атрибуты `class`, `id`, `src`, `href`, `width`, `height` — только
  текстовое содержимое.

## Стратегия по картинкам

Все картинки разделены на 3 группы:

1. **«Подпись + точки» — переводим подпись прямо на картинке** (через
   `work/translate_image_caption.py`, белая заливка верха + русский текст
   шрифтом DejaVu/Arial). Сохраняем в `out/images/`. Сюда входят:
   - 1-in-20.png — «Среднестатистическая выборка из 20 американских мужчин»
     + красная выноска «И только один из них выше 188 см»
   - gay-lesbian-bisexual.png — две колонки подписей
   - blind1.png — «1 из каждых 179 человек на земле слепой»
   - apple.png — «444 магазина Apple в мире»
   - flush.png — «508 раздач по 5 карт = 1 флеш»
   - millionaires.png — «1 из каждых 583 человек — миллионер»
   - princesses1.png — «48 настоящих принцесс»
   - neutron-star.png — «Нейтронная звезда делает 1 122 оборота в секунду»
   - minutes-in-a-day.png — «1 440 минут в сутках»
   - perfect-SAT1.png — «Только 1 из 1 489 получает 1600 на SAT»
   - exoplanets.png — «Астрономы нашли 1 849 экзопланет»
   - stars.png — «Ясной ночью видно ≈ 2 500 звёзд»
   - seconds-in-an-hour.png — «3 600 секунд в часе»
   - religions-in-the-world1.png — «4 200 религий в мире»
   - languages.png — «6 500 живых языков в мире (2 000 — с менее 1 000 носителей)»
   - sand1.png — «В кубическом сантиметре умещается 8 000 песчинок»
   - Craigslist.png — «В Craigslist около 40 сотрудников»

2. **Сложные диаграммы и крупные «подпись + точки» — оставляем
   английский текст в картинке, перевод даём в `<figcaption>` под
   изображением** (с компактным изложением подписей):
   - tetration-generally1.png
   - pentation-generally.png
   - hexation-generally1.png
   - string-bundle-examples1.png
   - grahams-festival.png
   - grahams-number.png
   - sun-tower1.png
   - insanity.png
   - g2.png
   - Fenway.png — «Столько людей собирается на распроданном Fenway Park (37 493)»
   - manhattan-buildings.png — «47 000 зданий на Манхэттене»
   - seconds-in-a-day.png — «86 400 секунд в сутках»
   - abortions1.png — «120 000 абортов в мире за сутки»

3. **Без значимого текста — не трогаем**:
   - 1-dot2-150x111.png, 1-dot2.png, 10-dots1.png, 100-dots1.png,
     1000-dots1.png, 10000-dots.png, 100000-dots.png, 1100th1.png,
     Million-Dots-one-red3.png, Moon.png (только мелкие технические
     метки/точки), million-poster_large.jpg, million-1in10000_large.jpg,
     million-1in100_large.jpg.

## Проблемы

- *abortions1.png*, *Fenway.png*, *manhattan-buildings.png*,
  *seconds-in-a-day.png* — очень большие изображения (высота
  до 6 200 пикселей). Английскую подпись внутри картинки оставляем
  без изменений, чтобы не пересохранять огромный PNG и не рисковать
  визуальной целостностью, а перевод даём отдельным `<figcaption>` под
  картинкой. Это разрешено критерием готовности.
- Кириллица в Apple System Font Geometric есть в Arial, Georgia,
  DejaVu, Noto Sans. Используем Arial Bold / Regular для совместимости с
  оригиналом.
- Подписи к комплексным диаграммам (тетрация и т. д.) даём в
  `<figcaption>` под картинкой с пометкой «Перевод подписей с
  диаграммы:».
