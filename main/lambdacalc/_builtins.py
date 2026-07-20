"""
内建算术运算：加、减、乘、除。

这些节点在 ``calculate`` 过程中支持常量折叠。
"""

from __future__ import annotations
from typing import Optional, Dict, Union
from ._core import Expr, Const


class BinOp(Expr):
    """二元运算基类。"""

    _prec: int  # 子类定义优先级
    _symbol: str  # 运算符号

    def __init__(self, left: Expr, right: Expr):
        self.left = left
        self.right = right

    # ------------------------------------------------------------------
    def _reduce_step(self, env: Dict[str, Expr]) -> Optional[Expr]:
        """尝试归约左/右子树，若两边均为常数则折叠。"""
        # 若左右均为常数 → 折叠
        if isinstance(self.left, Const) and isinstance(self.right, Const):
            return self._fold(self.left.value, self.right.value)
        # 否则，尝试归约左子树
        new_left = self.left._reduce_step(env)
        if new_left is not None:
            return self.__class__(new_left, self.right)
        # 再尝试归约右子树
        new_right = self.right._reduce_step(env)
        if new_right is not None:
            return self.__class__(self.left, new_right)
        return None

    def _fold(self, a: Union[int, float], b: Union[int, float]) -> Const:
        """子类实现具体运算。"""
        raise NotImplementedError

    def _to_string(self, outer_prec: int) -> str:
        # 左右操作数根据各自优先级决定是否加括号
        left_str = self.left._to_string(self._prec)
        right_str = self.right._to_string(self._prec + 1)  # 右操作数略微更高优先级
        s = f"{left_str} {self._symbol} {right_str}"
        if outer_prec > self._prec:
            return f"({s})"
        return s

    def _substitute(self, var_name: str, replacement: Expr) -> Expr:
        new_left = self.left._substitute(var_name, replacement)
        new_right = self.right._substitute(var_name, replacement)
        if new_left is self.left and new_right is self.right:
            return self
        return self.__class__(new_left, new_right)

    def _free_vars(self) -> set:
        return self.left._free_vars() | self.right._free_vars()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.left!r}, {self.right!r})"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.left == other.left and self.right == other.right
        return False

    def __hash__(self):
        return hash((self.__class__.__name__, self.left, self.right))


class Add(BinOp):
    """加法。"""
    _prec = 4
    _symbol = "+"

    def _fold(self, a, b) -> Const:
        return Const(a + b)


class Sub(BinOp):
    """减法。"""
    _prec = 4
    _symbol = "-"

    def _fold(self, a, b) -> Const:
        return Const(a - b)


class Mult(BinOp):
    """乘法。"""
    _prec = 5
    _symbol = "*"

    def _fold(self, a, b) -> Const:
        return Const(a * b)


class Div(BinOp):
    """除法（真除，结果为浮点数）。"""
    _prec = 5
    _symbol = "/"

    def _fold(self, a, b) -> Const:
        # 使用浮点除法，避免除零处理交给 Python 异常
        return Const(a / b)