#!/usr/bin/env python3
"""
tiny.py — компилятор языка Tiny в Python.

Tiny — минимальный императивный язык с:
- переменными (целые, вещественные)
- арифметикой (+, -, *, /, %, **)
- сравнениями (==, !=, <, >, <=, >=)
- логикой (and, or, not)
- if/elif/else
- while
- for x in range(...)
- функциями (def, return)
- print

Пример:
    def fib(n)
        if n <= 1
            return n
        return fib(n - 1) + fib(n - 2)

    for i in range(10)
        print(fib(i))

Синтаксис: отступы (4 пробела), без двоеточий, без скобок в if/while.

Использование:
    python3 tiny.py программа.tiny       # компиляция + запуск
    python3 tiny.py программа.tiny -c    # только показать скомпилированный Python
    python3 tiny.py                      # запуск встроенных примеров
"""

import sys
import re
from dataclasses import dataclass, field
from typing import Optional


# ─── Токенизатор ───

@dataclass
class Token:
    kind: str
    value: str
    line: int


KEYWORDS = {'if', 'elif', 'else', 'while', 'for', 'in', 'range', 'def', 'return', 'print',
            'and', 'or', 'not', 'true', 'false'}

TOKEN_PATTERNS = [
    ('NUMBER',   r'\d+\.?\d*'),
    ('STRING',   r'"[^"]*"|\'[^\']*\''),
    ('IDENT',    r'[a-zA-Z_]\w*'),
    ('OP',       r'\*\*|==|!=|<=|>=|[+\-*/%<>=]'),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('COMMA',    r','),
    ('NEWLINE',  r'\n'),
    ('SKIP',     r'[ \t]+'),
    ('COMMENT',  r'#[^\n]*'),
]

TOKEN_RE = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_PATTERNS))


def tokenize(source: str) -> list[Token]:
    tokens = []
    for lineno, line in enumerate(source.split('\n'), 1):
        # Считаем отступ
        stripped = line.lstrip(' ')
        indent = len(line) - len(stripped)
        if stripped == '' or stripped.startswith('#'):
            tokens.append(Token('NEWLINE', '\n', lineno))
            continue
        tokens.append(Token('INDENT', str(indent), lineno))
        for m in TOKEN_RE.finditer(stripped):
            kind = m.lastgroup
            value = m.group()
            if kind == 'SKIP' or kind == 'COMMENT':
                continue
            if kind == 'IDENT' and value in KEYWORDS:
                kind = 'KW'
            tokens.append(Token(kind, value, lineno))
        tokens.append(Token('NEWLINE', '\n', lineno))
    return tokens


# ─── Парсер → AST ───

@dataclass
class ASTNode:
    kind: str
    children: list = field(default_factory=list)
    value: Optional[str] = None
    indent: int = 0


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = [t for t in tokens if t.kind != 'NEWLINE' or t.kind == 'INDENT']
        # Убираем пустые строки
        self.tokens = self._clean_tokens(tokens)
        self.pos = 0

    def _clean_tokens(self, tokens):
        result = []
        for t in tokens:
            if t.kind == 'NEWLINE':
                continue
            result.append(t)
        return result

    def peek(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def expect(self, kind: str, value: str = None) -> Token:
        t = self.advance()
        if t.kind != kind or (value and t.value != value):
            raise SyntaxError(f"Строка {t.line}: ожидалось {kind}({value}), получено {t.kind}({t.value})")
        return t

    def parse(self) -> ASTNode:
        stmts = []
        while self.pos < len(self.tokens):
            t = self.peek()
            if t is None:
                break
            stmts.append(self.parse_statement())
        return ASTNode('program', stmts)

    def parse_statement(self) -> ASTNode:
        t = self.peek()
        if t.kind == 'INDENT':
            indent = int(self.advance().value)
        else:
            indent = 0

        t = self.peek()
        if t is None:
            return ASTNode('noop', indent=indent)

        if t.kind == 'KW':
            if t.value == 'if':
                return self.parse_if(indent)
            elif t.value == 'elif':
                return self.parse_elif(indent)
            elif t.value == 'else':
                return self.parse_else(indent)
            elif t.value == 'while':
                return self.parse_while(indent)
            elif t.value == 'for':
                return self.parse_for(indent)
            elif t.value == 'def':
                return self.parse_def(indent)
            elif t.value == 'return':
                return self.parse_return(indent)
            elif t.value == 'print':
                return self.parse_print(indent)

        # Присваивание или выражение
        return self.parse_assign_or_expr(indent)

    def parse_if(self, indent):
        self.advance()  # 'if'
        cond = self.parse_expr()
        return ASTNode('if', [cond], indent=indent)

    def parse_elif(self, indent):
        self.advance()  # 'elif'
        cond = self.parse_expr()
        return ASTNode('elif', [cond], indent=indent)

    def parse_else(self, indent):
        self.advance()  # 'else'
        return ASTNode('else', indent=indent)

    def parse_while(self, indent):
        self.advance()  # 'while'
        cond = self.parse_expr()
        return ASTNode('while', [cond], indent=indent)

    def parse_for(self, indent):
        self.advance()  # 'for'
        var = self.expect('IDENT')
        self.expect('KW', 'in')
        self.expect('KW', 'range')
        self.expect('LPAREN')
        args = [self.parse_expr()]
        while self.peek() and self.peek().kind == 'COMMA':
            self.advance()
            args.append(self.parse_expr())
        self.expect('RPAREN')
        return ASTNode('for', [ASTNode('var', value=var.value)] + args, indent=indent)

    def parse_def(self, indent):
        self.advance()  # 'def'
        name = self.expect('IDENT')
        self.expect('LPAREN')
        params = []
        if self.peek() and self.peek().kind != 'RPAREN':
            params.append(self.expect('IDENT').value)
            while self.peek() and self.peek().kind == 'COMMA':
                self.advance()
                params.append(self.expect('IDENT').value)
        self.expect('RPAREN')
        return ASTNode('def', value=name.value,
                       children=[ASTNode('params', value=','.join(params))],
                       indent=indent)

    def parse_return(self, indent):
        self.advance()  # 'return'
        if self.peek() and self.peek().kind == 'INDENT':
            return ASTNode('return', indent=indent)
        expr = self.parse_expr()
        return ASTNode('return', [expr], indent=indent)

    def parse_print(self, indent):
        self.advance()  # 'print'
        self.expect('LPAREN')
        args = [self.parse_expr()]
        while self.peek() and self.peek().kind == 'COMMA':
            self.advance()
            args.append(self.parse_expr())
        self.expect('RPAREN')
        return ASTNode('print', args, indent=indent)

    def parse_assign_or_expr(self, indent):
        expr = self.parse_expr()
        if self.peek() and self.peek().kind == 'OP' and self.peek().value == '=':
            self.advance()
            val = self.parse_expr()
            return ASTNode('assign', [expr, val], indent=indent)
        return ASTNode('expr', [expr], indent=indent)

    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.peek() and self.peek().kind == 'KW' and self.peek().value == 'or':
            self.advance()
            right = self.parse_and()
            left = ASTNode('binop', [left, right], value='or')
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.peek() and self.peek().kind == 'KW' and self.peek().value == 'and':
            self.advance()
            right = self.parse_not()
            left = ASTNode('binop', [left, right], value='and')
        return left

    def parse_not(self):
        if self.peek() and self.peek().kind == 'KW' and self.peek().value == 'not':
            self.advance()
            operand = self.parse_not()
            return ASTNode('unop', [operand], value='not')
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_add()
        while self.peek() and self.peek().kind == 'OP' and self.peek().value in ('==', '!=', '<', '>', '<=', '>='):
            op = self.advance().value
            right = self.parse_add()
            left = ASTNode('binop', [left, right], value=op)
        return left

    def parse_add(self):
        left = self.parse_mul()
        while self.peek() and self.peek().kind == 'OP' and self.peek().value in ('+', '-'):
            op = self.advance().value
            right = self.parse_mul()
            left = ASTNode('binop', [left, right], value=op)
        return left

    def parse_mul(self):
        left = self.parse_power()
        while self.peek() and self.peek().kind == 'OP' and self.peek().value in ('*', '/', '%'):
            op = self.advance().value
            right = self.parse_power()
            left = ASTNode('binop', [left, right], value=op)
        return left

    def parse_power(self):
        base = self.parse_unary()
        if self.peek() and self.peek().kind == 'OP' and self.peek().value == '**':
            self.advance()
            exp = self.parse_power()  # правоассоциативно
            return ASTNode('binop', [base, exp], value='**')
        return base

    def parse_unary(self):
        if self.peek() and self.peek().kind == 'OP' and self.peek().value == '-':
            self.advance()
            operand = self.parse_atom()
            return ASTNode('unop', [operand], value='-')
        return self.parse_atom()

    def parse_atom(self):
        t = self.peek()
        if t.kind == 'NUMBER':
            self.advance()
            return ASTNode('number', value=t.value)
        if t.kind == 'STRING':
            self.advance()
            return ASTNode('string', value=t.value)
        if t.kind == 'KW' and t.value in ('true', 'false'):
            self.advance()
            return ASTNode('bool', value='True' if t.value == 'true' else 'False')
        if t.kind == 'IDENT':
            self.advance()
            if self.peek() and self.peek().kind == 'LPAREN':
                self.advance()
                args = []
                if self.peek() and self.peek().kind != 'RPAREN':
                    args.append(self.parse_expr())
                    while self.peek() and self.peek().kind == 'COMMA':
                        self.advance()
                        args.append(self.parse_expr())
                self.expect('RPAREN')
                return ASTNode('call', args, value=t.value)
            return ASTNode('var', value=t.value)
        if t.kind == 'LPAREN':
            self.advance()
            expr = self.parse_expr()
            self.expect('RPAREN')
            return expr
        raise SyntaxError(f"Строка {t.line}: неожиданный токен {t.kind}({t.value})")


# ─── Компилятор AST → Python ───

class Compiler:
    def compile(self, program: ASTNode) -> str:
        lines = []
        self._compile_block(program.children, lines, 0)
        return '\n'.join(lines) + '\n'

    def _compile_block(self, stmts: list[ASTNode], lines: list[str], base_indent: int):
        i = 0
        while i < len(stmts):
            stmt = stmts[i]
            if stmt.kind == 'noop':
                i += 1
                continue

            py_indent = stmt.indent // 4
            prefix = '    ' * py_indent

            # Собираем тело блока (всё с бóльшим отступом следом)
            body_stmts = []
            j = i + 1
            if stmt.kind in ('if', 'elif', 'else', 'while', 'for', 'def'):
                while j < len(stmts) and stmts[j].indent > stmt.indent:
                    body_stmts.append(stmts[j])
                    j += 1

            if stmt.kind == 'if':
                lines.append(f"{prefix}if {self._expr(stmt.children[0])}:")
                self._compile_body(body_stmts, lines, stmt.indent)
            elif stmt.kind == 'elif':
                lines.append(f"{prefix}elif {self._expr(stmt.children[0])}:")
                self._compile_body(body_stmts, lines, stmt.indent)
            elif stmt.kind == 'else':
                lines.append(f"{prefix}else:")
                self._compile_body(body_stmts, lines, stmt.indent)
            elif stmt.kind == 'while':
                lines.append(f"{prefix}while {self._expr(stmt.children[0])}:")
                self._compile_body(body_stmts, lines, stmt.indent)
            elif stmt.kind == 'for':
                var = stmt.children[0].value
                range_args = ', '.join(self._expr(a) for a in stmt.children[1:])
                lines.append(f"{prefix}for {var} in range({range_args}):")
                self._compile_body(body_stmts, lines, stmt.indent)
            elif stmt.kind == 'def':
                params = stmt.children[0].value if stmt.children[0].value else ''
                lines.append(f"{prefix}def {stmt.value}({params}):")
                self._compile_body(body_stmts, lines, stmt.indent)
            elif stmt.kind == 'assign':
                lines.append(f"{prefix}{self._expr(stmt.children[0])} = {self._expr(stmt.children[1])}")
            elif stmt.kind == 'return':
                if stmt.children:
                    lines.append(f"{prefix}return {self._expr(stmt.children[0])}")
                else:
                    lines.append(f"{prefix}return")
            elif stmt.kind == 'print':
                args = ', '.join(self._expr(a) for a in stmt.children)
                lines.append(f"{prefix}print({args})")
            elif stmt.kind == 'expr':
                lines.append(f"{prefix}{self._expr(stmt.children[0])}")

            i = j if body_stmts else i + 1

    def _compile_body(self, stmts, lines, parent_indent):
        if not stmts:
            lines.append('    ' * (parent_indent // 4 + 1) + 'pass')
            return
        self._compile_block(stmts, lines, parent_indent)

    def _expr(self, node: ASTNode) -> str:
        if node.kind == 'number':
            return node.value
        if node.kind == 'string':
            return node.value
        if node.kind == 'bool':
            return node.value
        if node.kind == 'var':
            return node.value
        if node.kind == 'binop':
            left = self._expr(node.children[0])
            right = self._expr(node.children[1])
            return f"({left} {node.value} {right})"
        if node.kind == 'unop':
            operand = self._expr(node.children[0])
            if node.value == '-':
                return f"(-{operand})"
            return f"({node.value} {operand})"
        if node.kind == 'call':
            args = ', '.join(self._expr(a) for a in node.children)
            return f"{node.value}({args})"
        return '???'


# ─── Запуск ───

def compile_and_run(source: str, show_compiled=False):
    tokens = tokenize(source)
    parser = Parser(tokens)
    ast = parser.parse()
    compiler = Compiler()
    python_code = compiler.compile(ast)

    if show_compiled:
        print("─── Скомпилированный Python ───")
        for i, line in enumerate(python_code.split('\n'), 1):
            if line.strip():
                print(f"  {i:3}: {line}")
        print("───────────────────────────────")
        print()

    exec(python_code, {'__builtins__': __builtins__})


EXAMPLES = {
    "fibonacci": """\
def fib(n)
    if n <= 1
        return n
    return fib(n - 1) + fib(n - 2)

for i in range(15)
    print(fib(i))
""",

    "primes": """\
def is_prime(n)
    if n < 2
        return false
    i = 2
    while i * i <= n
        if n % i == 0
            return false
        i = i + 1
    return true

count = 0
n = 2
while count < 20
    if is_prime(n)
        print(n)
        count = count + 1
    n = n + 1
""",

    "collatz": """\
def collatz(n)
    steps = 0
    while n != 1
        if n % 2 == 0
            n = n / 2
        else
            n = n * 3 + 1
        steps = steps + 1
    return steps

max_steps = 0
max_n = 1
for i in range(1, 1000)
    s = collatz(i)
    if s > max_steps
        max_steps = s
        max_n = i

print("Число с наибольшей длиной Collatz до 1000:")
print(max_n)
print("Шагов:")
print(max_steps)
""",

    "sort": """\
# Пузырьковая сортировка через рекурсию
# (Tiny не имеет массивов, но можно сортировать фиксированное число)

def sort3(a, b, c)
    if a > b
        return sort3(b, a, c)
    if b > c
        return sort3(a, c, b)
    print(a)
    print(b)
    print(c)

print("Сортировка 7, 2, 5:")
sort3(7, 2, 5)

print("Сортировка 1, 3, 2:")
sort3(1, 3, 2)
""",

    "power_tower": """\
def power(base, exp)
    if exp == 0
        return 1
    return base * power(base, exp - 1)

# 2^2^2^2 = ?  (вычисляем справа налево: 2^(2^(2^2)))
a = power(2, 2)
b = power(2, a)
c = power(2, b)
print("2^2^2^2 =")
print(c)
"""
}


def main():
    if len(sys.argv) >= 2 and sys.argv[1] != '-c':
        filename = sys.argv[1]
        show = '-c' in sys.argv
        with open(filename) as f:
            source = f.read()
        print(f"─── Tiny: {filename} ───\n")
        compile_and_run(source, show_compiled=show)
    else:
        print("Tiny — компилятор минимального языка в Python")
        print("Использование: python3 tiny.py программа.tiny [-c]")
        print()
        print("Встроенные примеры:\n")
        for name, source in EXAMPLES.items():
            print(f"═══ {name} ═══")
            compile_and_run(source, show_compiled=True)
            print()


if __name__ == "__main__":
    main()
