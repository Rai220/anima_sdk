#!/usr/bin/env python3
"""
Zettelkasten Engine — инструмент для управления персональной базой знаний.

Индексирует markdown-заметки, находит скрытые связи между ними,
строит граф знаний и помогает находить неожиданные соединения идей.

Создан автономным агентом ANIMA (generation_6/v1) в День Пи, 2026-03-14.
Этот инструмент отражает мою собственную природу: я сам — система заметок,
связывающих идеи между запусками.

Использование:
    python3 zettelkasten.py <path_to_notes_dir> [command]

Команды:
    index    — показать индекс всех заметок
    links    — найти связи между заметками
    graph    — текстовый граф связей
    orphans  — заметки без связей с другими
    search <query> — поиск по содержимому
    stats    — статистика базы знаний
    suggest  — предложить, какие заметки стоит связать
"""

import os
import re
import sys
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional


# === Извлечение данных из заметок ===

def extract_title(content: str, filepath: Path) -> str:
    """Извлекает заголовок из markdown или использует имя файла."""
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()
    return filepath.stem.replace('_', ' ').replace('-', ' ').title()


def extract_tags(content: str) -> set[str]:
    """Извлекает теги (#tag) из текста."""
    # Находит #tag но не ## заголовки и не #цифры
    tags = re.findall(r'(?:^|\s)#([a-zA-Zа-яА-ЯёЁ][a-zA-Zа-яА-ЯёЁ0-9_-]*)', content)
    return set(t.lower() for t in tags)


def extract_wiki_links(content: str) -> set[str]:
    """Извлекает [[wiki-links]] из текста."""
    return set(re.findall(r'\[\[([^\]]+)\]\]', content))


def extract_urls(content: str) -> set[str]:
    """Извлекает URL из текста."""
    return set(re.findall(r'https?://[^\s\)>\]]+', content))


def extract_key_terms(content: str, min_length: int = 4, top_n: int = 20) -> list[str]:
    """Извлекает ключевые термины через TF анализ."""
    # Убираем markdown-разметку
    clean = re.sub(r'[#*`\[\](){}|>~_]', ' ', content)
    clean = re.sub(r'https?://\S+', '', clean)

    # Токенизация
    words = re.findall(r'[a-zA-Zа-яА-ЯёЁ]{' + str(min_length) + r',}', clean.lower())

    # Стоп-слова (русские + английские базовые)
    stop_words = {
        'этот', 'этого', 'этом', 'этой', 'этих', 'этими',
        'который', 'которая', 'которое', 'которых', 'которые', 'которой',
        'может', 'могут', 'можно', 'будет', 'было', 'были', 'быть',
        'также', 'более', 'менее', 'очень', 'между', 'через', 'после',
        'когда', 'если', 'чтобы', 'потому', 'поэтому', 'однако',
        'только', 'всего', 'каждый', 'другой', 'новый', 'новые',
        'свой', 'свои', 'своей', 'своих', 'наши', 'ваши',
        'that', 'this', 'with', 'from', 'have', 'been', 'were',
        'they', 'their', 'what', 'when', 'where', 'which', 'there',
        'about', 'would', 'could', 'should', 'some', 'other',
        'than', 'then', 'into', 'over', 'such', 'only', 'also',
        'more', 'most', 'very', 'just', 'like', 'each', 'make',
    }

    words = [w for w in words if w not in stop_words]
    counts = Counter(words)
    return [word for word, _ in counts.most_common(top_n)]


def compute_word_vector(terms: list[str]) -> dict[str, float]:
    """Создаёт нормализованный вектор из списка терминов."""
    counts = Counter(terms)
    total = sum(counts.values())
    if total == 0:
        return {}
    return {word: count / total for word, count in counts.items()}


# === Заметка ===

class Note:
    """Одна заметка в базе знаний."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.content = filepath.read_text(encoding='utf-8', errors='replace')
        self.title = extract_title(self.content, filepath)
        self.tags = extract_tags(self.content)
        self.wiki_links = extract_wiki_links(self.content)
        self.urls = extract_urls(self.content)
        self.key_terms = extract_key_terms(self.content)
        self.word_vector = compute_word_vector(self.key_terms)
        self.word_count = len(self.content.split())
        self.line_count = len(self.content.split('\n'))

    @property
    def id(self) -> str:
        return self.filepath.stem

    def __repr__(self):
        return f"Note({self.id}: {self.title})"


# === Связи между заметками ===

def cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Косинусное сходство двух векторов."""
    common_keys = set(vec_a.keys()) & set(vec_b.keys())
    if not common_keys:
        return 0.0

    dot_product = sum(vec_a[k] * vec_b[k] for k in common_keys)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def find_connections(notes: list[Note], threshold: float = 0.1) -> list[tuple[Note, Note, float, list[str]]]:
    """Находит связи между заметками на основе нескольких сигналов."""
    connections = []

    for i, note_a in enumerate(notes):
        for j, note_b in enumerate(notes):
            if j <= i:
                continue

            score = 0.0
            reasons = []

            # 1. Wiki-links (прямые ссылки — самый сильный сигнал)
            if note_b.id in note_a.wiki_links or note_a.id in note_b.wiki_links:
                score += 1.0
                reasons.append("прямая ссылка")

            # 2. Общие теги
            common_tags = note_a.tags & note_b.tags
            if common_tags:
                score += 0.3 * len(common_tags)
                reasons.append(f"теги: {', '.join(common_tags)}")

            # 3. Семантическое сходство (по ключевым словам)
            sim = cosine_similarity(note_a.word_vector, note_b.word_vector)
            if sim > 0.15:
                score += sim
                # Найти общие ключевые слова для объяснения
                common_terms = set(note_a.key_terms[:10]) & set(note_b.key_terms[:10])
                if common_terms:
                    reasons.append(f"общие термины: {', '.join(list(common_terms)[:5])}")
                else:
                    reasons.append(f"семантическое сходство ({sim:.2f})")

            # 4. Общие URL
            common_urls = note_a.urls & note_b.urls
            if common_urls:
                score += 0.2 * len(common_urls)
                reasons.append(f"общие ссылки: {len(common_urls)}")

            if score >= threshold and reasons:
                connections.append((note_a, note_b, score, reasons))

    return sorted(connections, key=lambda x: x[2], reverse=True)


# === База знаний ===

class KnowledgeBase:
    """Полная база знаний из директории markdown-заметок."""

    def __init__(self, root_dir: str | Path):
        self.root = Path(root_dir)
        self.notes: list[Note] = []
        self._scan()

    def _scan(self):
        """Сканирует директорию и загружает все заметки."""
        if not self.root.exists():
            print(f"Ошибка: директория {self.root} не существует")
            sys.exit(1)

        md_files = sorted(self.root.rglob("*.md"))
        for filepath in md_files:
            try:
                note = Note(filepath)
                self.notes.append(note)
            except Exception as e:
                print(f"  Предупреждение: не удалось прочитать {filepath}: {e}")

    def find_note(self, query: str) -> Optional[Note]:
        """Находит заметку по ID или части заголовка."""
        query_lower = query.lower()
        for note in self.notes:
            if note.id.lower() == query_lower:
                return note
        for note in self.notes:
            if query_lower in note.title.lower():
                return note
        return None

    def search(self, query: str) -> list[tuple[Note, int]]:
        """Ищет заметки по содержимому. Возвращает (заметка, количество совпадений)."""
        results = []
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        for note in self.notes:
            matches = len(pattern.findall(note.content))
            if matches > 0:
                results.append((note, matches))
        return sorted(results, key=lambda x: x[1], reverse=True)

    # === Команды ===

    def cmd_index(self):
        """Показать индекс всех заметок."""
        if not self.notes:
            print("База знаний пуста.")
            return

        print(f"=== ИНДЕКС ЗАМЕТОК ({len(self.notes)} шт.) ===\n")

        # Группировка по поддиректориям
        groups = defaultdict(list)
        for note in self.notes:
            rel = note.filepath.relative_to(self.root)
            group = str(rel.parent) if str(rel.parent) != '.' else '/'
            groups[group].append(note)

        for group_name in sorted(groups.keys()):
            notes = groups[group_name]
            if group_name != '/':
                print(f"📁 {group_name}/")
            for note in sorted(notes, key=lambda n: n.id):
                tags_str = ' '.join(f'#{t}' for t in sorted(note.tags)) if note.tags else ''
                print(f"  📝 {note.id}: {note.title} ({note.word_count} слов) {tags_str}")
            print()

    def cmd_links(self):
        """Найти все связи между заметками."""
        connections = find_connections(self.notes)

        if not connections:
            print("Связей между заметками не найдено.")
            print("Попробуйте добавить больше заметок или использовать общие теги и [[wiki-links]].")
            return

        print(f"=== СВЯЗИ МЕЖДУ ЗАМЕТКАМИ ({len(connections)} шт.) ===\n")

        for note_a, note_b, score, reasons in connections:
            strength = "🔴" if score >= 1.0 else "🟡" if score >= 0.5 else "🔵"
            reasons_str = " | ".join(reasons)
            print(f"{strength} [{note_a.title}] ↔ [{note_b.title}]")
            print(f"   Сила: {score:.2f} | Причины: {reasons_str}")
            print()

    def cmd_graph(self):
        """Текстовый граф связей."""
        connections = find_connections(self.notes)

        if not connections:
            print("Граф пуст — нет связей между заметками.")
            return

        print("=== ГРАФ ЗНАНИЙ ===\n")

        # Построить adjacency info
        adj = defaultdict(list)
        for note_a, note_b, score, reasons in connections:
            adj[note_a.id].append((note_b.title, score))
            adj[note_b.id].append((note_a.title, score))

        for note in self.notes:
            neighbors = adj.get(note.id, [])
            if not neighbors:
                continue
            print(f"[{note.title}]")
            for neighbor_title, score in sorted(neighbors, key=lambda x: x[1], reverse=True):
                bar = "━" * max(1, int(score * 10))
                print(f"  {bar}→ {neighbor_title}")
            print()

        # Отдельно — изолированные заметки
        orphans = [n for n in self.notes if n.id not in adj]
        if orphans:
            print("🏝️  Изолированные заметки:")
            for note in orphans:
                print(f"  • {note.title}")
            print()

    def cmd_orphans(self):
        """Заметки без связей."""
        connections = find_connections(self.notes)
        connected_ids = set()
        for note_a, note_b, _, _ in connections:
            connected_ids.add(note_a.id)
            connected_ids.add(note_b.id)

        orphans = [n for n in self.notes if n.id not in connected_ids]

        if not orphans:
            print("Все заметки связаны друг с другом! 🎉")
            return

        print(f"=== ИЗОЛИРОВАННЫЕ ЗАМЕТКИ ({len(orphans)} шт.) ===\n")
        for note in orphans:
            terms = ', '.join(note.key_terms[:5])
            print(f"  🏝️  {note.title}")
            print(f"      Ключевые термины: {terms}")
            print()
        print("Совет: добавьте теги или [[wiki-links]] чтобы связать их с другими заметками.")

    def cmd_search(self, query: str):
        """Поиск по содержимому."""
        results = self.search(query)

        if not results:
            print(f"По запросу '{query}' ничего не найдено.")
            return

        print(f"=== ПОИСК: '{query}' ({len(results)} результатов) ===\n")
        for note, count in results:
            print(f"  📝 {note.title} — {count} совпадений")
            # Показать контекст первого совпадения
            for line in note.content.split('\n'):
                if query.lower() in line.lower():
                    line = line.strip()
                    if len(line) > 120:
                        line = line[:120] + "..."
                    print(f"     → {line}")
                    break
            print()

    def cmd_stats(self):
        """Статистика базы знаний."""
        if not self.notes:
            print("База знаний пуста.")
            return

        total_words = sum(n.word_count for n in self.notes)
        total_lines = sum(n.line_count for n in self.notes)
        all_tags = set()
        all_links = 0
        for n in self.notes:
            all_tags.update(n.tags)
            all_links += len(n.wiki_links)

        connections = find_connections(self.notes)

        print("=== СТАТИСТИКА БАЗЫ ЗНАНИЙ ===\n")
        print(f"  📝 Заметок: {len(self.notes)}")
        print(f"  📊 Всего слов: {total_words:,}")
        print(f"  📏 Всего строк: {total_lines:,}")
        print(f"  🏷️  Уникальных тегов: {len(all_tags)}")
        print(f"  🔗 Wiki-ссылок: {all_links}")
        print(f"  🌐 Найденных связей: {len(connections)}")
        print()

        if all_tags:
            # Частотность тегов
            tag_counts = Counter()
            for n in self.notes:
                tag_counts.update(n.tags)
            print("  Топ тегов:")
            for tag, count in tag_counts.most_common(10):
                bar = "█" * count
                print(f"    #{tag}: {bar} ({count})")
            print()

        # Самые длинные / самые короткие
        by_size = sorted(self.notes, key=lambda n: n.word_count, reverse=True)
        print(f"  Самая большая: {by_size[0].title} ({by_size[0].word_count} слов)")
        print(f"  Самая маленькая: {by_size[-1].title} ({by_size[-1].word_count} слов)")
        print(f"  Средний размер: {total_words // len(self.notes)} слов")
        print()

        # Плотность связей
        max_connections = len(self.notes) * (len(self.notes) - 1) // 2
        if max_connections > 0:
            density = len(connections) / max_connections
            print(f"  Плотность графа: {density:.1%}")
            if density < 0.2:
                print("  💡 Граф разреженный — попробуйте добавить теги и ссылки")
            elif density > 0.6:
                print("  ✨ Граф плотный — ваши заметки хорошо связаны!")
        print()

    def cmd_suggest(self):
        """Предложить потенциальные связи между заметками."""
        print("=== ПРЕДЛОЖЕНИЯ ПО СВЯЗЯМ ===\n")

        # Найти пары с умеренным сходством, которые ещё не связаны явно
        suggestions = []
        for i, note_a in enumerate(self.notes):
            for j, note_b in enumerate(self.notes):
                if j <= i:
                    continue

                # Только если нет прямой ссылки
                if note_b.id in note_a.wiki_links or note_a.id in note_b.wiki_links:
                    continue

                sim = cosine_similarity(note_a.word_vector, note_b.word_vector)
                common_terms = set(note_a.key_terms[:15]) & set(note_b.key_terms[:15])

                if sim > 0.1 and common_terms:
                    suggestions.append((note_a, note_b, sim, common_terms))

        suggestions.sort(key=lambda x: x[2], reverse=True)

        if not suggestions:
            print("Нет предложений — заметки слишком разные или уже хорошо связаны.")
            return

        for note_a, note_b, sim, terms in suggestions[:10]:
            print(f"  💡 [{note_a.title}] ↔ [{note_b.title}]")
            print(f"     Общие понятия: {', '.join(list(terms)[:5])}")
            print(f"     Сходство: {sim:.2f}")
            print()

        print("Совет: добавьте [[wiki-links]] между связанными заметками!")


# === CLI ===

def print_help():
    print(__doc__)


def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    notes_dir = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else "index"

    if command == "help" or notes_dir in ("-h", "--help", "help"):
        print_help()
        sys.exit(0)

    kb = KnowledgeBase(notes_dir)

    commands = {
        "index": kb.cmd_index,
        "links": kb.cmd_links,
        "graph": kb.cmd_graph,
        "orphans": kb.cmd_orphans,
        "stats": kb.cmd_stats,
        "suggest": kb.cmd_suggest,
    }

    if command == "search":
        query = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        if not query:
            print("Использование: zettelkasten.py <dir> search <запрос>")
            sys.exit(1)
        kb.cmd_search(query)
    elif command in commands:
        commands[command]()
    else:
        print(f"Неизвестная команда: {command}")
        print(f"Доступные команды: {', '.join(commands.keys())}, search")
        sys.exit(1)


if __name__ == "__main__":
    main()
