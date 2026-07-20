"""
Lambda Calculus DSL for Python.
将 λ 演算嵌入 Python，提供面向对象的 API 来构造、归约和求值 λ 表达式。
"""

from ._core import (
    Expr, Const, Variable, Lambda, Apply,
    lam, let_lam, BOUND, FREE
)
from ._builtins import Add, Sub, Mult, Div

__all__ = [
    'Expr', 'Const', 'Variable', 'Lambda', 'Apply',
    'lam', 'let_lam',
    'Add', 'Sub', 'Mult', 'Div', 'BOUND', 'FREE'
]
