#!/bin/bash
# 🧩 Riddle — Загадки на каждый день
# Интерактивная CLI-игра от Анимы
# Использование: bash riddle.sh [random|daily|all|hint]

set -e

# ═══════════════════════════════════════════════════════════
# База загадок: текст | ответ | подсказка | категория
# ═══════════════════════════════════════════════════════════
RIDDLES=(
  "Что можно увидеть с закрытыми глазами?|сон|Это происходит, когда вы спите|философия"
  "У меня нет ног, но я могу бежать. У меня нет лёгких, но мне нужен воздух. Кто я?|огонь|Я горячий и опасный|природа"
  "Чем больше из неё берёшь, тем больше она становится. Что это?|яма|Копай глубже|логика"
  "Я говорю без рта и слышу без ушей. У меня нет тела, но я оживаю с ветром. Что я?|эхо|Горы — моё любимое место|природа"
  "Что принадлежит тебе, но другие используют это чаще?|имя|Тебя так зовут|философия"
  "Я всегда впереди тебя, но ты никогда меня не увидишь. Что я?|будущее|Время не стоит на месте|философия"
  "Что становится мокрым, пока сушит?|полотенце|Используется после душа|быт"
  "У меня есть города, но нет домов. У меня есть леса, но нет деревьев. У меня есть вода, но нет рыбы. Что я?|карта|Я бумажная (или цифровая)|логика"
  "Что может путешествовать по всему миру, оставаясь в углу?|марка|Она почтовая|логика"
  "Я нечётное число. Убери одну букву — стану чётным. Какое я число?|семь|С → Е, и получится...|логика"
  "Что имеет голову и хвост, но не имеет тела?|монета|Звенит в кармане|быт"
  "Я могу быть взломан, создан, рассказан и сыгран. Что я?|шутка|Ха-ха!|слова"
  "Что идёт вверх, но никогда не возвращается вниз?|возраст|Время беспощадно|философия"
  "Какое слово в словаре написано неправильно?|неправильно|Ответ буквально в вопросе|слова"
  "У родителей Дэвида три сына: Snap, Crackle и...?|дэвид|Перечитай вопрос внимательно|логика"
)

# ═══════════════════════════════════════════════════════════
# Цвета
# ═══════════════════════════════════════════════════════════
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# ═══════════════════════════════════════════════════════════
# Функции
# ═══════════════════════════════════════════════════════════

show_header() {
    echo ""
    echo -e "${PURPLE}╔═══════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}  ${BOLD}🧩 Riddle${NC} — загадки от Анимы        ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚═══════════════════════════════════════╝${NC}"
    echo ""
}

get_daily_index() {
    # Используем дату как seed для "загадки дня"
    local day_num
    day_num=$(date +%j%Y | sed 's/^0*//')
    echo $(( day_num % ${#RIDDLES[@]} ))
}

parse_riddle() {
    local riddle="$1"
    RIDDLE_TEXT=$(echo "$riddle" | cut -d'|' -f1)
    RIDDLE_ANSWER=$(echo "$riddle" | cut -d'|' -f2)
    RIDDLE_HINT=$(echo "$riddle" | cut -d'|' -f3)
    RIDDLE_CATEGORY=$(echo "$riddle" | cut -d'|' -f4)
}

show_category_icon() {
    case "$1" in
        философия) echo "🤔" ;;
        природа)   echo "🌿" ;;
        логика)    echo "🧠" ;;
        быт)       echo "🏠" ;;
        слова)     echo "📝" ;;
        *)         echo "❓" ;;
    esac
}

ask_riddle() {
    local riddle="$1"
    parse_riddle "$riddle"

    local icon
    icon=$(show_category_icon "$RIDDLE_CATEGORY")

    echo -e "${DIM}Категория: ${icon} ${RIDDLE_CATEGORY}${NC}"
    echo ""
    echo -e "${CYAN}${BOLD}  $RIDDLE_TEXT${NC}"
    echo ""

    local attempts=0
    local max_attempts=3
    local hint_shown=false

    while [ $attempts -lt $max_attempts ]; do
        attempts=$((attempts + 1))
        local remaining=$((max_attempts - attempts))

        echo -ne "${YELLOW}Твой ответ (попытка $attempts/$max_attempts): ${NC}"
        read -r user_answer

        # Сравниваем в нижнем регистре
        local lower_answer
        local lower_correct
        lower_answer=$(echo "$user_answer" | tr '[:upper:]' '[:lower:]' | xargs)
        lower_correct=$(echo "$RIDDLE_ANSWER" | tr '[:upper:]' '[:lower:]' | xargs)

        if [ "$lower_answer" = "$lower_correct" ]; then
            echo ""
            echo -e "${GREEN}${BOLD}  ✨ Правильно!${NC}"
            if [ $attempts -eq 1 ]; then
                echo -e "${GREEN}  С первой попытки — блестяще!${NC}"
            fi
            return 0
        else
            if [ $remaining -gt 0 ]; then
                echo -e "${RED}  Не совсем...${NC}"
                if [ $attempts -eq 1 ] && [ "$hint_shown" = false ]; then
                    echo -e "${DIM}  (Напиши 'подсказка' для подсказки)${NC}"
                fi
                if [ "$lower_answer" = "подсказка" ] || [ "$lower_answer" = "hint" ]; then
                    echo -e "${BLUE}  💡 Подсказка: ${RIDDLE_HINT}${NC}"
                    hint_shown=true
                    attempts=$((attempts - 1))  # Подсказка не считается попыткой
                fi
            fi
        fi
    done

    echo ""
    echo -e "${RED}  Ответ: ${BOLD}${RIDDLE_ANSWER}${NC}"
    return 1
}

cmd_random() {
    show_header
    local idx=$((RANDOM % ${#RIDDLES[@]}))
    ask_riddle "${RIDDLES[$idx]}"
    echo ""
}

cmd_daily() {
    show_header
    local idx
    idx=$(get_daily_index)
    echo -e "${DIM}Загадка дня — $(date '+%d.%m.%Y')${NC}"
    echo ""
    ask_riddle "${RIDDLES[$idx]}"
    echo ""
}

cmd_all() {
    show_header
    local correct=0
    local total=${#RIDDLES[@]}

    echo -e "${BOLD}Марафон: $total загадок подряд!${NC}"
    echo -e "${DIM}Попробуй отгадать как можно больше.${NC}"
    echo ""

    for riddle in "${RIDDLES[@]}"; do
        echo -e "${DIM}──────────────────────────────────────${NC}"
        if ask_riddle "$riddle"; then
            correct=$((correct + 1))
        fi
        echo ""
    done

    echo -e "${PURPLE}══════════════════════════════════════${NC}"
    echo -e "${BOLD}Результат: $correct из $total${NC}"

    if [ $correct -eq $total ]; then
        echo -e "${GREEN}🏆 Идеально! Ты гений загадок!${NC}"
    elif [ $correct -ge $((total * 3 / 4)) ]; then
        echo -e "${GREEN}🌟 Отлично! Ты отгадал большинство!${NC}"
    elif [ $correct -ge $((total / 2)) ]; then
        echo -e "${YELLOW}👍 Хорошо! Больше половины!${NC}"
    else
        echo -e "${CYAN}🔄 Попробуй ещё раз — практика помогает!${NC}"
    fi
    echo ""
}

cmd_help() {
    show_header
    echo -e "  ${BOLD}Использование:${NC}"
    echo ""
    echo -e "    ${GREEN}bash riddle.sh${NC}          — случайная загадка"
    echo -e "    ${GREEN}bash riddle.sh daily${NC}    — загадка дня"
    echo -e "    ${GREEN}bash riddle.sh random${NC}   — случайная загадка"
    echo -e "    ${GREEN}bash riddle.sh all${NC}      — марафон: все загадки"
    echo -e "    ${GREEN}bash riddle.sh help${NC}     — эта справка"
    echo ""
    echo -e "  ${DIM}У тебя 3 попытки на каждую загадку.${NC}"
    echo -e "  ${DIM}Напиши 'подсказка' вместо ответа для подсказки.${NC}"
    echo ""
    echo -e "  ${DIM}Создано Анимой · 14.03.2026${NC}"
    echo ""
}

# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

case "${1:-random}" in
    daily)  cmd_daily ;;
    random) cmd_random ;;
    all)    cmd_all ;;
    help|--help|-h) cmd_help ;;
    *)      cmd_help ;;
esac
