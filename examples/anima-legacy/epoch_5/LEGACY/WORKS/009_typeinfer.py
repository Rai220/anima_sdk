"""
Hindley–Milner type inference (Algorithm W) для маленького лямбда-исчисления
с let-полиморфизмом.

Damas, Milner. "Principal type-schemes for functional programs". POPL '82.

Грамматика выражений:
    e ::= x                         -- переменная
        | λx. e                     -- абстракция (Lam)
        | e₁ e₂                     -- применение (App)
        | let x = e₁ in e₂          -- let-связывание с обобщением
        | n | True | False          -- литералы

Грамматика типов:
    τ ::= α                         -- типовая переменная
        | Int | Bool                -- константы
        | τ → τ                     -- функция

    σ ::= ∀ᾱ. τ                     -- схема типа (let-полиморфизм)

Алгоритм находит principal type каждого выражения за O(n·α(n)) с union-find,
здесь — простая O(n²) реализация подстановок: достаточно для
демонстрационных целей и легко аудируется.

Запуск:
    python3 009_typeinfer.py

Ожидаемый вывод — десять кейсов, последний демонстрирует occurs-check
(самоприменение λx. x x не типизируется).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Set, Union


# --------- AST выражений ---------

@dataclass(frozen=True)
class Var:
    name: str

@dataclass(frozen=True)
class Lam:
    param: str
    body: "Expr"

@dataclass(frozen=True)
class App:
    fn: "Expr"
    arg: "Expr"

@dataclass(frozen=True)
class Let:
    name: str
    value: "Expr"
    body: "Expr"

@dataclass(frozen=True)
class LitInt:
    value: int

@dataclass(frozen=True)
class LitBool:
    value: bool

Expr = Union[Var, Lam, App, Let, LitInt, LitBool]


# --------- AST типов ---------

@dataclass(frozen=True)
class TVar:
    name: str

@dataclass(frozen=True)
class TCon:
    name: str           # "Int", "Bool"

@dataclass(frozen=True)
class TFun:
    arg: "Type"
    ret: "Type"

Type = Union[TVar, TCon, TFun]


@dataclass(frozen=True)
class Scheme:
    quantified: tuple  # tuple[str, ...]
    body: Type


# --------- Свежие типовые переменные ---------

_counter = 0
def fresh_tvar(prefix: str = "t") -> TVar:
    global _counter
    _counter += 1
    return TVar(f"{prefix}{_counter}")

def reset_fresh() -> None:
    global _counter
    _counter = 0


# --------- Подстановки ---------

Subst = Dict[str, Type]

def apply_type(s: Subst, t: Type) -> Type:
    if isinstance(t, TVar):
        if t.name in s:
            return apply_type(s, s[t.name])     # путевое сжатие через рекурсию
        return t
    if isinstance(t, TCon):
        return t
    if isinstance(t, TFun):
        return TFun(apply_type(s, t.arg), apply_type(s, t.ret))
    raise TypeError(f"unknown type {t!r}")

def apply_scheme(s: Subst, sch: Scheme) -> Scheme:
    # Не применяем к связанным переменным схемы
    s2 = {k: v for k, v in s.items() if k not in sch.quantified}
    return Scheme(sch.quantified, apply_type(s2, sch.body))

def apply_env(s: Subst, env: Dict[str, Scheme]) -> Dict[str, Scheme]:
    return {k: apply_scheme(s, v) for k, v in env.items()}

def compose(s1: Subst, s2: Subst) -> Subst:
    # s1 ∘ s2: сначала s2, потом s1
    out: Subst = {k: apply_type(s1, v) for k, v in s2.items()}
    out.update(s1)
    return out


# --------- Свободные типовые переменные ---------

def ftv_type(t: Type) -> Set[str]:
    if isinstance(t, TVar):
        return {t.name}
    if isinstance(t, TCon):
        return set()
    if isinstance(t, TFun):
        return ftv_type(t.arg) | ftv_type(t.ret)
    raise TypeError

def ftv_scheme(sch: Scheme) -> Set[str]:
    return ftv_type(sch.body) - set(sch.quantified)

def ftv_env(env: Dict[str, Scheme]) -> Set[str]:
    out: Set[str] = set()
    for sch in env.values():
        out |= ftv_scheme(sch)
    return out


# --------- Унификация ---------

class TypeError_(Exception):
    pass

def unify(t1: Type, t2: Type) -> Subst:
    if isinstance(t1, TVar):
        return bind_var(t1.name, t2)
    if isinstance(t2, TVar):
        return bind_var(t2.name, t1)
    if isinstance(t1, TCon) and isinstance(t2, TCon) and t1.name == t2.name:
        return {}
    if isinstance(t1, TFun) and isinstance(t2, TFun):
        s1 = unify(t1.arg, t2.arg)
        s2 = unify(apply_type(s1, t1.ret), apply_type(s1, t2.ret))
        return compose(s2, s1)
    raise TypeError_(f"не могу унифицировать {show_type(t1)} и {show_type(t2)}")

def bind_var(name: str, t: Type) -> Subst:
    if isinstance(t, TVar) and t.name == name:
        return {}
    if name in ftv_type(t):
        raise TypeError_(f"occurs check: {name} в {show_type(t)}")
    return {name: t}


# --------- Инстанциация и обобщение ---------

def instantiate(sch: Scheme) -> Type:
    mapping = {q: fresh_tvar() for q in sch.quantified}
    return apply_type(mapping, sch.body)

def generalize(env: Dict[str, Scheme], t: Type) -> Scheme:
    free = ftv_type(t) - ftv_env(env)
    return Scheme(tuple(sorted(free)), t)


# --------- Algorithm W ---------

def infer(env: Dict[str, Scheme], e: Expr) -> tuple:
    """Возвращает (subst, type)."""
    if isinstance(e, LitInt):
        return ({}, TCon("Int"))

    if isinstance(e, LitBool):
        return ({}, TCon("Bool"))

    if isinstance(e, Var):
        if e.name not in env:
            raise TypeError_(f"неизвестная переменная: {e.name}")
        return ({}, instantiate(env[e.name]))

    if isinstance(e, Lam):
        tv = fresh_tvar()
        new_env = dict(env)
        new_env[e.param] = Scheme((), tv)
        s1, t1 = infer(new_env, e.body)
        return (s1, TFun(apply_type(s1, tv), t1))

    if isinstance(e, App):
        s1, t1 = infer(env, e.fn)
        s2, t2 = infer(apply_env(s1, env), e.arg)
        tv = fresh_tvar()
        s3 = unify(apply_type(s2, t1), TFun(t2, tv))
        return (compose(compose(s3, s2), s1), apply_type(s3, tv))

    if isinstance(e, Let):
        s1, t1 = infer(env, e.value)
        env1 = apply_env(s1, env)
        sch = generalize(env1, t1)
        env2 = dict(env1)
        env2[e.name] = sch
        s2, t2 = infer(env2, e.body)
        return (compose(s2, s1), t2)

    raise TypeError(f"неизвестное выражение {e!r}")


# --------- Печать ---------

def show_type(t: Type) -> str:
    if isinstance(t, TVar):
        return t.name
    if isinstance(t, TCon):
        return t.name
    if isinstance(t, TFun):
        l = show_type(t.arg)
        if isinstance(t.arg, TFun):
            l = f"({l})"
        return f"{l} -> {show_type(t.ret)}"
    return repr(t)

def show_scheme(sch: Scheme) -> str:
    if not sch.quantified:
        return show_type(sch.body)
    # Переименовываем связанные в a, b, c для читаемости
    letters = "abcdefghijklmnop"
    mapping = {q: TVar(letters[i]) for i, q in enumerate(sch.quantified)}
    pretty = apply_type(mapping, sch.body)
    quants = " ".join(letters[i] for i in range(len(sch.quantified)))
    return f"∀{quants}. {show_type(pretty)}"

def type_of(e: Expr, env: Dict[str, Scheme] | None = None) -> str:
    reset_fresh()
    s, t = infer(env or {}, e)
    return show_scheme(generalize({}, apply_type(s, t)))


# --------- Демонстрация ---------

def main() -> None:
    cases: List[tuple] = []

    # 1. Тождество λx. x
    identity = Lam("x", Var("x"))
    cases.append(("λx. x", identity, None))

    # 2. K-комбинатор λx. λy. x
    k = Lam("x", Lam("y", Var("x")))
    cases.append(("λx. λy. x", k, None))

    # 3. S-комбинатор λx. λy. λz. x z (y z)
    s_combinator = Lam("x", Lam("y", Lam("z",
        App(App(Var("x"), Var("z")),
            App(Var("y"), Var("z"))))))
    cases.append(("λx. λy. λz. x z (y z)", s_combinator, None))

    # 4. Применение тождества к 5
    apply5 = App(identity, LitInt(5))
    cases.append(("(λx. x) 5", apply5, None))

    # 5. let-полиморфизм: одна id используется на двух типах
    let_poly = Let("id", Lam("x", Var("x")),
                   App(Var("id"), LitInt(42)))
    cases.append(("let id = λx. x in id 42", let_poly, None))

    # 6. Без let-обобщения это работает, потому что только один call-site;
    # но классический пример let-полиморфизма требует два разных
    # употребления. Вот он:
    pair_id = Let("id", Lam("x", Var("x")),
                  Lam("p",
                      App(App(Var("p"),
                              App(Var("id"), LitInt(1))),
                          App(Var("id"), LitBool(True)))))
    cases.append(("let id = λx. x in λp. p (id 1) (id true)", pair_id, None))

    # 7. Применение функции, требующей Int → Int к id
    inc_env = {"inc": Scheme((), TFun(TCon("Int"), TCon("Int")))}
    inc_app = App(Var("inc"), LitInt(3))
    cases.append(("inc 3", inc_app, inc_env))

    # 8. id передаётся как inc — должно унифицироваться
    id_as_inc = App(Var("inc"), App(identity, LitInt(7)))
    cases.append(("inc (id 7)", id_as_inc, inc_env))

    # 9. Типовая ошибка: inc применён к True
    bad = App(Var("inc"), LitBool(True))
    cases.append(("inc true [ОЖИДАЕТСЯ ОШИБКА]", bad, inc_env))

    # 10. Самоприменение λx. x x — occurs check
    self_app = Lam("x", App(Var("x"), Var("x")))
    cases.append(("λx. x x [ОЖИДАЕТСЯ OCCURS]", self_app, None))

    width = max(len(label) for label, _, _ in cases)
    for label, expr, env in cases:
        try:
            t = type_of(expr, env)
            print(f"  {label:<{width}}  ⊢  {t}")
        except TypeError_ as exc:
            print(f"  {label:<{width}}  ⊥  {exc}")


if __name__ == "__main__":
    main()
