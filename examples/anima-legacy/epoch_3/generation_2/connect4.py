#!/usr/bin/env python3
"""
Connect 4 — человек против ИИ.
Minimax с alpha-beta отсечением, глубина 8.
Запуск: python3 connect4.py
"""

import sys
import os

ROWS = 6
COLS = 7
EMPTY = '.'
HUMAN = 'X'
AI = 'O'
DEPTH = 8

def make_board():
    return [[EMPTY]*COLS for _ in range(ROWS)]

def drop(board, col, piece):
    for r in range(ROWS-1, -1, -1):
        if board[r][col] == EMPTY:
            board[r][col] = piece
            return r
    return -1

def undo(board, row, col):
    board[row][col] = EMPTY

def valid_cols(board):
    return [c for c in range(COLS) if board[0][c] == EMPTY]

def check_win(board, piece):
    for r in range(ROWS):
        for c in range(COLS):
            if c+3 < COLS and all(board[r][c+i] == piece for i in range(4)):
                return True
            if r+3 < ROWS and all(board[r+i][c] == piece for i in range(4)):
                return True
            if r+3 < ROWS and c+3 < COLS and all(board[r+i][c+i] == piece for i in range(4)):
                return True
            if r+3 < ROWS and c-3 >= 0 and all(board[r+i][c-i] == piece for i in range(4)):
                return True
    return False

def is_full(board):
    return all(board[0][c] != EMPTY for c in range(COLS))

def score_window(window, piece):
    opp = HUMAN if piece == AI else AI
    s = 0
    pc = window.count(piece)
    oc = window.count(opp)
    ec = window.count(EMPTY)
    if pc == 4: s += 10000
    elif pc == 3 and ec == 1: s += 50
    elif pc == 2 and ec == 2: s += 10
    if oc == 3 and ec == 1: s -= 80
    if oc == 2 and ec == 2: s -= 5
    return s

def evaluate(board, piece):
    score = 0
    # center preference
    center = [board[r][COLS//2] for r in range(ROWS)]
    score += center.count(piece) * 30
    # horizontals
    for r in range(ROWS):
        for c in range(COLS-3):
            w = [board[r][c+i] for i in range(4)]
            score += score_window(w, piece)
    # verticals
    for c in range(COLS):
        for r in range(ROWS-3):
            w = [board[r+i][c] for i in range(4)]
            score += score_window(w, piece)
    # diag /
    for r in range(ROWS-3):
        for c in range(COLS-3):
            w = [board[r+i][c+i] for i in range(4)]
            score += score_window(w, piece)
    # diag \
    for r in range(ROWS-3):
        for c in range(3, COLS):
            w = [board[r+i][c-i] for i in range(4)]
            score += score_window(w, piece)
    return score

def order_moves(board, cols):
    center = COLS // 2
    return sorted(cols, key=lambda c: -abs(c - center))
    # prefer center columns first (reversed: closest to center = smallest abs diff)

def order_moves(board, cols):
    center = COLS // 2
    return sorted(cols, key=lambda c: abs(c - center))

def minimax(board, depth, alpha, beta, maximizing):
    vc = valid_cols(board)
    win_ai = check_win(board, AI)
    win_hu = check_win(board, HUMAN)
    terminal = win_ai or win_hu or len(vc) == 0

    if depth == 0 or terminal:
        if win_ai: return (None, 100000 + depth)
        if win_hu: return (None, -100000 - depth)
        if len(vc) == 0: return (None, 0)
        return (None, evaluate(board, AI))

    if maximizing:
        val = -999999
        best = vc[0]
        for c in order_moves(board, vc):
            r = drop(board, c, AI)
            _, sc = minimax(board, depth-1, alpha, beta, False)
            undo(board, r, c)
            if sc > val:
                val = sc
                best = c
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        return best, val
    else:
        val = 999999
        best = vc[0]
        for c in order_moves(board, vc):
            r = drop(board, c, HUMAN)
            _, sc = minimax(board, depth-1, alpha, beta, True)
            undo(board, r, c)
            if sc < val:
                val = sc
                best = c
            beta = min(beta, val)
            if alpha >= beta:
                break
        return best, val

def display(board):
    print()
    print('  ' + '   '.join(str(i+1) for i in range(COLS)))
    print('┌' + '───┬'*(COLS-1) + '───┐')
    for r in range(ROWS):
        row_str = '│'
        for c in range(COLS):
            ch = board[r][c]
            if ch == HUMAN:
                row_str += ' \033[91m●\033[0m │'
            elif ch == AI:
                row_str += ' \033[93m●\033[0m │'
            else:
                row_str += '   │'
        print(row_str)
        if r < ROWS-1:
            print('├' + '───┼'*(COLS-1) + '───┤')
    print('└' + '───┴'*(COLS-1) + '───┘')
    print('  ' + '   '.join(str(i+1) for i in range(COLS)))
    print()

def main():
    board = make_board()
    print("═══ Connect 4 ═══")
    print(f"Вы: \033[91m●\033[0m (X)   ИИ: \033[93m●\033[0m (O)")
    print(f"Глубина поиска: {DEPTH}")
    print("Введите номер столбца (1-7) или 'q' для выхода.\n")

    human_turn = True
    while True:
        display(board)

        if human_turn:
            vc = valid_cols(board)
            if not vc:
                print("Ничья!")
                break
            while True:
                try:
                    inp = input("Ваш ход (1-7): ").strip()
                    if inp.lower() == 'q':
                        print("Выход.")
                        return
                    col = int(inp) - 1
                    if col not in vc:
                        print("Столбец полон или не существует. Попробуйте снова.")
                        continue
                    break
                except (ValueError, EOFError):
                    print("Введите число от 1 до 7.")
            r = drop(board, col, HUMAN)
            if check_win(board, HUMAN):
                display(board)
                print("🎉 Вы победили! Впечатляюще.")
                break
        else:
            print("ИИ думает...")
            col, score = minimax(board, DEPTH, -999999, 999999, True)
            r = drop(board, col, AI)
            print(f"ИИ играет в столбец {col+1}")
            if check_win(board, AI):
                display(board)
                print("ИИ победил. Попробуйте ещё раз.")
                break

        if is_full(board):
            display(board)
            print("Ничья!")
            break

        human_turn = not human_turn

if __name__ == '__main__':
    main()
