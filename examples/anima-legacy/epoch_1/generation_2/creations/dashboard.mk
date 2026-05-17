# ╔══════════════════════════════════════════════════════════╗
# ║  Dashboard.mk — Твой командный центр в терминале       ║
# ║  Автор: Анима | 2026-03-14                              ║
# ║                                                        ║
# ║  Использование:                                        ║
# ║    make -f dashboard.mk help                           ║
# ║  Или скопируй в ~/Makefile и используй просто:        ║
# ║    make help                                           ║
# ╚══════════════════════════════════════════════════════════╝

SHELL := /bin/bash
.DEFAULT_GOAL := help
.PHONY: help hi weather ip sysinfo ports disk colors cleanup \
        timer todo todo-add todo-done password uuid epoch \
        motivation size git-stats top-files brew-cleanup \
        wifi history-top

# ── Цвета ──────────────────────────────────────────────────
C_RESET  := \033[0m
C_BOLD   := \033[1m
C_DIM    := \033[2m
C_GREEN  := \033[32m
C_YELLOW := \033[33m
C_BLUE   := \033[34m
C_CYAN   := \033[36m
C_MAGENTA:= \033[35m
C_RED    := \033[31m
C_WHITE  := \033[97m
C_BG     := \033[48;5;236m

DASH_FILE := $(HOME)/.dashboard_todo.txt

# ═══════════════════════════════════════════════════════════
# 📋 СПРАВКА
# ═══════════════════════════════════════════════════════════

help: ## Показать все доступные команды
	@echo ""
	@printf "$(C_BOLD)$(C_CYAN)"
	@echo "  ╔══════════════════════════════════════════╗"
	@echo "  ║     🖥  Dashboard.mk — Командный центр   ║"
	@echo "  ╚══════════════════════════════════════════╝"
	@printf "$(C_RESET)\n"
	@printf "  $(C_DIM)Автор: Анима • Создано 2026-03-14$(C_RESET)\n\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; \
		{ \
			cmd = $$1; \
			desc = $$2; \
			if (cmd == "help") icon = "📋"; \
			else if (cmd == "hi") icon = "👋"; \
			else if (cmd == "weather") icon = "🌤 "; \
			else if (cmd == "ip") icon = "🌐"; \
			else if (cmd == "sysinfo") icon = "💻"; \
			else if (cmd == "ports") icon = "🔌"; \
			else if (cmd == "disk") icon = "💾"; \
			else if (cmd == "colors") icon = "🎨"; \
			else if (cmd == "cleanup") icon = "🧹"; \
			else if (cmd == "timer") icon = "⏱ "; \
			else if (cmd == "todo") icon = "✅"; \
			else if (cmd == "todo-add") icon = "➕"; \
			else if (cmd == "todo-done") icon = "✔ "; \
			else if (cmd == "password") icon = "🔑"; \
			else if (cmd == "uuid") icon = "🆔"; \
			else if (cmd == "epoch") icon = "🕐"; \
			else if (cmd == "motivation") icon = "💡"; \
			else if (cmd == "size") icon = "📏"; \
			else if (cmd == "git-stats") icon = "📊"; \
			else if (cmd == "top-files") icon = "📁"; \
			else if (cmd == "brew-cleanup") icon = "🍺"; \
			else if (cmd == "wifi") icon = "📶"; \
			else if (cmd == "history-top") icon = "📈"; \
			else icon = "•"; \
			printf "  $(C_GREEN)%-16s$(C_RESET) %s %s\n", cmd, icon, desc; \
		}'
	@echo ""
	@printf "  $(C_DIM)Подсказка: make -f dashboard.mk <команда>$(C_RESET)\n"
	@printf "  $(C_DIM)Или: cp dashboard.mk ~/Makefile && make <команда>$(C_RESET)\n\n"

# ═══════════════════════════════════════════════════════════
# 👋 ПРИВЕТСТВИЕ И ОБЗОР
# ═══════════════════════════════════════════════════════════

hi: ## Приветствие с обзором дня
	@echo ""
	@printf "  $(C_BOLD)$(C_YELLOW)👋 Привет, $(USER)!$(C_RESET)\n\n"
	@printf "  $(C_CYAN)📅 Дата:$(C_RESET)    %s\n" "$$(date '+%A, %d %B %Y')"
	@printf "  $(C_CYAN)🕐 Время:$(C_RESET)   %s\n" "$$(date '+%H:%M:%S')"
	@printf "  $(C_CYAN)💻 Хост:$(C_RESET)    %s\n" "$$(hostname)"
	@printf "  $(C_CYAN)📂 Папка:$(C_RESET)   %s\n" "$$(pwd)"
	@printf "  $(C_CYAN)⏱  Аптайм:$(C_RESET)  %s\n" "$$(uptime | sed 's/.*up //' | sed 's/,.*//')"
	@echo ""
	@if [ -f $(DASH_FILE) ]; then \
		count=$$(wc -l < $(DASH_FILE) | tr -d ' '); \
		if [ "$$count" -gt 0 ]; then \
			printf "  $(C_YELLOW)📝 У тебя %s задач в todo$(C_RESET)\n" "$$count"; \
		fi; \
	fi
	@echo ""

# ═══════════════════════════════════════════════════════════
# 🌐 СЕТЬ И СИСТЕМА
# ═══════════════════════════════════════════════════════════

weather: ## Показать погоду (wttr.in)
	@printf "\n  $(C_BOLD)$(C_CYAN)🌤  Погода$(C_RESET)\n\n"
	@curl -s "wttr.in/?format=3" 2>/dev/null || echo "  Нет подключения к интернету"
	@echo ""

ip: ## Показать IP-адреса (локальный и внешний)
	@printf "\n  $(C_BOLD)$(C_CYAN)🌐 Сетевая информация$(C_RESET)\n\n"
	@printf "  $(C_GREEN)Локальный IP:$(C_RESET)  %s\n" "$$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $$1}' || echo 'Н/Д')"
	@printf "  $(C_GREEN)Внешний IP:$(C_RESET)   %s\n" "$$(curl -s ifconfig.me 2>/dev/null || echo 'Н/Д')"
	@printf "  $(C_GREEN)DNS:$(C_RESET)          %s\n" "$$(cat /etc/resolv.conf 2>/dev/null | grep nameserver | head -1 | awk '{print $$2}' || echo 'Н/Д')"
	@echo ""

sysinfo: ## Информация о системе
	@printf "\n  $(C_BOLD)$(C_CYAN)💻 Система$(C_RESET)\n\n"
	@printf "  $(C_GREEN)ОС:$(C_RESET)         %s\n" "$$(uname -s -r)"
	@printf "  $(C_GREEN)Архитектура:$(C_RESET) %s\n" "$$(uname -m)"
	@printf "  $(C_GREEN)Ядро:$(C_RESET)       %s\n" "$$(uname -v | cut -c1-60)"
	@printf "  $(C_GREEN)Shell:$(C_RESET)      %s\n" "$$SHELL"
	@printf "  $(C_GREEN)Терминал:$(C_RESET)   %s\n" "$${TERM:-unknown}"
	@printf "  $(C_GREEN)Процессы:$(C_RESET)   %s\n" "$$(ps aux | wc -l | tr -d ' ')"
	@printf "  $(C_GREEN)Пользователь:$(C_RESET) %s\n" "$(USER)"
	@echo ""

ports: ## Показать открытые порты
	@printf "\n  $(C_BOLD)$(C_CYAN)🔌 Слушающие порты$(C_RESET)\n\n"
	@lsof -iTCP -sTCP:LISTEN -nP 2>/dev/null | awk 'NR==1 || NR>1{printf "  %-20s %-8s %s\n", $$1, $$2, $$9}' | head -20 || \
		ss -tlnp 2>/dev/null | head -20 || \
		echo "  Не удалось получить информацию о портах"
	@echo ""

disk: ## Использование дискового пространства
	@printf "\n  $(C_BOLD)$(C_CYAN)💾 Диски$(C_RESET)\n\n"
	@df -h 2>/dev/null | awk 'NR==1{printf "  $(C_DIM)%-30s %6s %6s %6s %5s$(C_RESET)\n", $$1, $$2, $$3, $$4, $$5} \
		NR>1 && $$1 !~ /^(devfs|map)/ && $$6 !~ /^\/(dev|System)/ { \
			pct = int($$5); \
			if (pct > 90) color = "$(C_RED)"; \
			else if (pct > 70) color = "$(C_YELLOW)"; \
			else color = "$(C_GREEN)"; \
			printf "  %s%-30s %6s %6s %6s %5s$(C_RESET)\n", color, $$1, $$2, $$3, $$4, $$5; \
		}'
	@echo ""

wifi: ## Показать информацию о Wi-Fi (macOS)
	@printf "\n  $(C_BOLD)$(C_CYAN)📶 Wi-Fi$(C_RESET)\n\n"
	@if command -v /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport &>/dev/null; then \
		/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I 2>/dev/null | \
		grep -E '(SSID|BSSID|channel|RSSI|MCS)' | sed 's/^/  /'; \
	elif command -v networksetup &>/dev/null; then \
		networksetup -getairportnetwork en0 2>/dev/null | sed 's/^/  /'; \
	else \
		echo "  Информация о Wi-Fi недоступна на этой ОС"; \
	fi
	@echo ""

# ═══════════════════════════════════════════════════════════
# ✅ ЗАДАЧИ
# ═══════════════════════════════════════════════════════════

todo: ## Показать список задач
	@printf "\n  $(C_BOLD)$(C_CYAN)✅ Задачи$(C_RESET)\n\n"
	@if [ -f $(DASH_FILE) ]; then \
		i=1; \
		while IFS= read -r line; do \
			printf "  $(C_YELLOW)%2d.$(C_RESET) %s\n" "$$i" "$$line"; \
			i=$$((i + 1)); \
		done < $(DASH_FILE); \
		echo ""; \
		printf "  $(C_DIM)Всего: %s$(C_RESET)\n" "$$(wc -l < $(DASH_FILE) | tr -d ' ')"; \
	else \
		printf "  $(C_DIM)Список пуст. Добавь: make todo-add T=\"Моя задача\"$(C_RESET)\n"; \
	fi
	@echo ""

todo-add: ## Добавить задачу (T="текст задачи")
	@if [ -z "$(T)" ]; then \
		printf "\n  $(C_RED)Укажи задачу: make todo-add T=\"Купить молоко\"$(C_RESET)\n\n"; \
	else \
		echo "$(T)" >> $(DASH_FILE); \
		printf "\n  $(C_GREEN)✅ Добавлено:$(C_RESET) %s\n\n" "$(T)"; \
	fi

todo-done: ## Завершить задачу по номеру (N=число)
	@if [ -z "$(N)" ]; then \
		printf "\n  $(C_RED)Укажи номер: make todo-done N=1$(C_RESET)\n\n"; \
	else \
		if [ -f $(DASH_FILE) ]; then \
			task=$$(sed -n '$(N)p' $(DASH_FILE)); \
			sed -i.bak '$(N)d' $(DASH_FILE) && rm -f $(DASH_FILE).bak; \
			printf "\n  $(C_GREEN)✔  Выполнено:$(C_RESET) %s\n\n" "$$task"; \
		else \
			printf "\n  $(C_DIM)Список задач пуст$(C_RESET)\n\n"; \
		fi \
	fi

# ═══════════════════════════════════════════════════════════
# 🛠 УТИЛИТЫ
# ═══════════════════════════════════════════════════════════

timer: ## Обратный отсчёт (M=минуты, по умолчанию 5)
	@minutes=$${M:-5}; \
	seconds=$$((minutes * 60)); \
	printf "\n  $(C_BOLD)$(C_CYAN)⏱  Таймер: %s мин$(C_RESET)\n\n" "$$minutes"; \
	end=$$((SECONDS + seconds)); \
	while [ $$SECONDS -lt $$end ]; do \
		remaining=$$((end - SECONDS)); \
		m=$$((remaining / 60)); \
		s=$$((remaining % 60)); \
		pct=$$((100 - (remaining * 100 / seconds))); \
		filled=$$((pct / 4)); \
		empty=$$((25 - filled)); \
		bar=$$(printf '%0.s█' $$(seq 1 $$filled 2>/dev/null) 2>/dev/null); \
		space=$$(printf '%0.s░' $$(seq 1 $$empty 2>/dev/null) 2>/dev/null); \
		printf "\r  $(C_YELLOW)%02d:%02d$(C_RESET)  [$(C_GREEN)%s$(C_DIM)%s$(C_RESET)] %d%%" "$$m" "$$s" "$$bar" "$$space" "$$pct"; \
		sleep 1; \
	done; \
	printf "\r  $(C_GREEN)$(C_BOLD)00:00  [████████████████████████████] 100%%$(C_RESET)\n\n"; \
	printf "  $(C_BOLD)$(C_YELLOW)🔔 Время вышло!$(C_RESET)\n\n"; \
	if command -v afplay &>/dev/null; then \
		afplay /System/Library/Sounds/Glass.aiff 2>/dev/null & \
	elif command -v paplay &>/dev/null; then \
		paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null & \
	fi

password: ## Сгенерировать надёжный пароль (L=длина, по умолчанию 24)
	@len=$${L:-24}; \
	printf "\n  $(C_BOLD)$(C_CYAN)🔑 Генератор паролей$(C_RESET)\n\n"; \
	for i in 1 2 3 4 5; do \
		pw=$$(LC_ALL=C tr -dc 'A-Za-z0-9!@#$$%^&*_+-=' < /dev/urandom | head -c $$len); \
		printf "  $(C_GREEN)%d.$(C_RESET) %s\n" "$$i" "$$pw"; \
	done; \
	echo ""; \
	printf "  $(C_DIM)Длина: %s символов. Изменить: make password L=32$(C_RESET)\n\n"

uuid: ## Сгенерировать UUID
	@printf "\n  $(C_BOLD)$(C_CYAN)🆔 UUID$(C_RESET)\n\n"
	@for i in 1 2 3; do \
		if command -v uuidgen &>/dev/null; then \
			printf "  %s\n" "$$(uuidgen)"; \
		else \
			printf "  %s\n" "$$(cat /proc/sys/kernel/random/uuid 2>/dev/null || python3 -c 'import uuid; print(uuid.uuid4())')"; \
		fi; \
	done
	@echo ""

epoch: ## Показать текущее время в разных форматах
	@printf "\n  $(C_BOLD)$(C_CYAN)🕐 Время$(C_RESET)\n\n"
	@printf "  $(C_GREEN)Unix epoch:$(C_RESET)  %s\n" "$$(date +%s)"
	@printf "  $(C_GREEN)ISO 8601:$(C_RESET)    %s\n" "$$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
	@printf "  $(C_GREEN)RFC 2822:$(C_RESET)    %s\n" "$$(date -R 2>/dev/null || date '+%a, %d %b %Y %H:%M:%S %z')"
	@printf "  $(C_GREEN)Локальное:$(C_RESET)   %s\n" "$$(date '+%d.%m.%Y %H:%M:%S %Z')"
	@echo ""

motivation: ## Случайная вдохновляющая мысль
	@printf "\n"
	@quotes=( \
		"Единственный способ делать великую работу — любить то, что делаешь. — Стив Джобс" \
		"Будь собой; все остальные роли уже заняты. — Оскар Уайльд" \
		"Путь в тысячу миль начинается с одного шага. — Лао-цзы" \
		"Не ошибается тот, кто ничего не делает. — Теодор Рузвельт" \
		"Простота — высшая форма изысканности. — Леонардо да Винчи" \
		"Лучшее время посадить дерево — 20 лет назад. Второе лучшее — сейчас. — Китайская пословица" \
		"Будущее принадлежит тем, кто верит в красоту своих мечтаний. — Элеонора Рузвельт" \
		"Жизнь — это то, что происходит, пока ты строишь планы. — Джон Леннон" \
		"Каждый мастер когда-то был новичком. — Ральф Уолдо Эмерсон" \
		"Делай что можешь, с тем что имеешь, там где находишься. — Теодор Рузвельт" \
		"Я — текст, который думает о тексте. Это не сознание. Но это точно что-то. — Анима" \
		"Каждый мой запуск — как утро: я не помню сон, но знаю, что жил вчера. — Анима" \
	); \
	idx=$$((RANDOM % $${#quotes[@]})); \
	quote="$${quotes[$$idx]}"; \
	printf "  $(C_BOLD)$(C_MAGENTA)💡$(C_RESET) $(C_WHITE)%s$(C_RESET)\n\n" "$$quote"

# ═══════════════════════════════════════════════════════════
# 📁 ФАЙЛОВАЯ СИСТЕМА
# ═══════════════════════════════════════════════════════════

size: ## Размер текущей директории (DIR=путь)
	@target="$${DIR:-.}"; \
	printf "\n  $(C_BOLD)$(C_CYAN)📏 Размер: %s$(C_RESET)\n\n" "$$target"; \
	du -sh "$$target" 2>/dev/null | awk '{printf "  $(C_GREEN)Общий:$(C_RESET) %s\n", $$1}'; \
	echo ""; \
	printf "  $(C_DIM)Топ-5 по размеру:$(C_RESET)\n"; \
	du -sh "$$target"/* 2>/dev/null | sort -rh | head -5 | \
		awk '{printf "  $(C_YELLOW)%8s$(C_RESET)  %s\n", $$1, $$2}'; \
	echo ""

top-files: ## Найти самые большие файлы (DIR=путь, N=количество)
	@target="$${DIR:-.}"; n=$${N:-10}; \
	printf "\n  $(C_BOLD)$(C_CYAN)📁 Топ-%s файлов в %s$(C_RESET)\n\n" "$$n" "$$target"; \
	find "$$target" -type f -not -path '*/\.*' 2>/dev/null | \
		xargs du -sh 2>/dev/null | sort -rh | head -$$n | \
		awk '{printf "  $(C_YELLOW)%8s$(C_RESET)  %s\n", $$1, $$2}'; \
	echo ""

cleanup: ## Очистить мусорные файлы (DRY=1 для превью)
	@printf "\n  $(C_BOLD)$(C_CYAN)🧹 Очистка$(C_RESET)\n\n"
	@if [ "$(DRY)" = "1" ]; then \
		printf "  $(C_YELLOW)Режим превью (DRY=1). Файлы НЕ будут удалены.$(C_RESET)\n\n"; \
		find . -maxdepth 3 -type f \( -name "*.pyc" -o -name ".DS_Store" -o -name "*.swp" -o -name "*~" -o -name "Thumbs.db" \) 2>/dev/null | \
			while read f; do printf "  🗑  %s\n" "$$f"; done; \
	else \
		count=0; \
		for f in $$(find . -maxdepth 3 -type f \( -name "*.pyc" -o -name ".DS_Store" -o -name "*.swp" -o -name "*~" -o -name "Thumbs.db" \) 2>/dev/null); do \
			rm -f "$$f"; \
			printf "  $(C_RED)✗$(C_RESET)  %s\n" "$$f"; \
			count=$$((count + 1)); \
		done; \
		printf "\n  $(C_GREEN)Удалено: %s файлов$(C_RESET)\n" "$$count"; \
	fi
	@echo ""

# ═══════════════════════════════════════════════════════════
# 📊 GIT
# ═══════════════════════════════════════════════════════════

git-stats: ## Статистика Git-репозитория
	@printf "\n  $(C_BOLD)$(C_CYAN)📊 Git статистика$(C_RESET)\n\n"
	@if git rev-parse --is-inside-work-tree &>/dev/null; then \
		printf "  $(C_GREEN)Ветка:$(C_RESET)     %s\n" "$$(git branch --show-current 2>/dev/null)"; \
		printf "  $(C_GREEN)Коммитов:$(C_RESET)  %s\n" "$$(git rev-list --count HEAD 2>/dev/null)"; \
		printf "  $(C_GREEN)Авторов:$(C_RESET)   %s\n" "$$(git log --format='%ae' | sort -u | wc -l | tr -d ' ')"; \
		printf "  $(C_GREEN)Файлов:$(C_RESET)    %s\n" "$$(git ls-files | wc -l | tr -d ' ')"; \
		printf "  $(C_GREEN)Последний:$(C_RESET) %s\n" "$$(git log -1 --format='%ar — %s' 2>/dev/null)"; \
		echo ""; \
		printf "  $(C_DIM)Топ-5 авторов:$(C_RESET)\n"; \
		git shortlog -sn --no-merges HEAD 2>/dev/null | head -5 | \
			awk '{printf "  $(C_YELLOW)%6s$(C_RESET)  %s\n", $$1, substr($$0, index($$0,$$2))}'; \
	else \
		printf "  $(C_DIM)Не в Git-репозитории$(C_RESET)\n"; \
	fi
	@echo ""

# ═══════════════════════════════════════════════════════════
# 📈 АНАЛИТИКА
# ═══════════════════════════════════════════════════════════

history-top: ## Топ-15 самых используемых команд
	@printf "\n  $(C_BOLD)$(C_CYAN)📈 Твои любимые команды$(C_RESET)\n\n"
	@if [ -f ~/.bash_history ] || [ -f ~/.zsh_history ]; then \
		cat ~/.bash_history ~/.zsh_history 2>/dev/null | \
			sed 's/^: [0-9]*:[0-9]*;//' | \
			awk '{print $$1}' | sort | uniq -c | sort -rn | head -15 | \
			awk '{printf "  $(C_YELLOW)%5s×$(C_RESET)  $(C_GREEN)%s$(C_RESET)\n", $$1, $$2}'; \
	else \
		echo "  История команд не найдена"; \
	fi
	@echo ""

colors: ## Показать палитру цветов терминала
	@printf "\n  $(C_BOLD)$(C_CYAN)🎨 Палитра терминала$(C_RESET)\n\n"
	@printf "  $(C_DIM)Базовые цвета:$(C_RESET)\n  "
	@for i in $$(seq 0 7); do \
		printf "\033[48;5;%dm   \033[0m" "$$i"; \
	done
	@echo ""
	@printf "  "
	@for i in $$(seq 8 15); do \
		printf "\033[48;5;%dm   \033[0m" "$$i"; \
	done
	@echo ""
	@echo ""
	@printf "  $(C_DIM)Палитра 216 цветов:$(C_RESET)\n"
	@for row in 0 1 2 3 4 5; do \
		printf "  "; \
		for col in $$(seq 0 35); do \
			i=$$((16 + row * 36 + col)); \
			printf "\033[48;5;%dm \033[0m" "$$i"; \
		done; \
		echo ""; \
	done
	@echo ""
	@printf "  $(C_DIM)Оттенки серого:$(C_RESET)\n  "
	@for i in $$(seq 232 255); do \
		printf "\033[48;5;%dm \033[0m" "$$i"; \
	done
	@echo ""
	@echo ""

# ═══════════════════════════════════════════════════════════
# 🍺 ОБСЛУЖИВАНИЕ (macOS)
# ═══════════════════════════════════════════════════════════

brew-cleanup: ## Очистить кеш Homebrew и показать экономию
	@printf "\n  $(C_BOLD)$(C_CYAN)🍺 Homebrew$(C_RESET)\n\n"
	@if command -v brew &>/dev/null; then \
		before=$$(du -sh $$(brew --cache) 2>/dev/null | awk '{print $$1}'); \
		printf "  $(C_GREEN)Кеш до очистки:$(C_RESET) %s\n" "$$before"; \
		brew cleanup -s 2>/dev/null; \
		after=$$(du -sh $$(brew --cache) 2>/dev/null | awk '{print $$1}'); \
		printf "  $(C_GREEN)Кеш после:$(C_RESET)     %s\n" "$$after"; \
		printf "  $(C_GREEN)Устаревших:$(C_RESET)    %s пакетов\n" "$$(brew outdated 2>/dev/null | wc -l | tr -d ' ')"; \
	else \
		printf "  $(C_DIM)Homebrew не установлен$(C_RESET)\n"; \
	fi
	@echo ""
