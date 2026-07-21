"""
核心表达式类与求值逻辑。

提供 λ 演算的抽象语法树节点：变量、常量、抽象、应用，
以及构造组合子的函数 `lam`, `let_lam`。
"""

from __future__ import annotations
from typing import Optional, Union, List, Dict
from ._utils import warn_yellow, fresh_var_name


# ---------------------------------------------------------------------------
# 表达式基类
# ---------------------------------------------------------------------------

class Expr:
    """所有 λ 表达式节点的抽象基类。"""

    # 优先级，用于 building() 省略括号（数值越大越“紧”，括号越少）
    _prec: int = 10  # 默认最高（原子）

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def beta(self, arg: Expr) -> 'Apply':
        """返回应用表达式 ``(self arg)``，不执行任何归约。

        Parameters
        ----------
        arg : Expr
            参数表达式。

        Returns
        -------
        Apply
            应用节点 ``Apply(self, arg)``。
        """
        return Apply(self, arg)

    def calculate(self, env: List['Variable']) -> Union[int, float, 'Expr']:
        """在给定环境下将表达式归约到范式（正常序）。

        Parameters
        ----------
        env : list of Variable
            已赋值的自由变量列表。每个 ``Variable`` 对象若已调用
            ``assign(value)``，则其值将在归约时用于替换同名自由变量。

        Returns
        -------
        int or float or Expr
            若最终范式为数字常量，直接返回 Python 数字；
            否则返回范式表达式（可能是抽象、应用或含自由变量的节点）。
        """
        # 构建替换字典（自由变量名 -> 表达式）
        subs: Dict[str, Expr] = {}
        for v in env:
            if v.kind != 'free':
                continue
            if v.value is not None:
                subs[v.name] = v.value

        expr = self
        while True:
            nxt = expr._reduce_step(subs)
            if nxt is None:
                break
            expr = nxt

        # 结果若是常数且为数字，则“拆箱”
        if isinstance(expr, Const) and isinstance(expr.value, (int, float)):
            return expr.value
        return expr

    def building(self) -> str:
        """返回表达式的完全字符串表示，使用 ``λ``，尽可能省略括号。"""
        return self._to_string(0)

    # ------------------------------------------------------------------
    # 内部方法（子类按需覆盖）
    # ------------------------------------------------------------------

    def _reduce_step(self, env: Dict[str, Expr]) -> Optional[Expr]:
        """尝试执行**一步**正常序归约。

        Parameters
        ----------
        env : dict
            自由变量名到其值（表达式）的映射。

        Returns
        -------
        Expr or None
            归约一步后的表达式；若无法再归约则返回 None。
        """
        return None  # 默认不可归约

    def _to_string(self, outer_prec: int) -> str:
        """带优先级控制的字符串化。

        Parameters
        ----------
        outer_prec : int
            外部上下文要求的最小优先级。若自身优先级更低，需加括号。
        """
        raise NotImplementedError

    def _substitute(self, var_name: str, replacement: Expr) -> Expr:
        """将体内所有**自由出现**的 ``var_name`` 替换为 ``replacement``。

        自动进行 α 转换以避免变量捕获。
        """
        raise NotImplementedError

    def _free_vars(self) -> set:
        """返回表达式中的自由变量名集合。"""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

class Const(Expr):
    """字面常量（Python 数值）。"""

    def __init__(self, value: Union[int, float]):
        self.value = value

    def _to_string(self, outer_prec: int) -> str:
        return str(self.value)

    def _substitute(self, var_name: str, replacement: Expr) -> Expr:
        return self  # 常数内无变量

    def _free_vars(self) -> set:
        return set()

    def __repr__(self):
        return f"Const({self.value})"

    def __eq__(self, other):
        if isinstance(other, Const):
            return self.value == other.value
        return False

    def __hash__(self):
        return hash(('Const', self.value))


# ---------------------------------------------------------------------------
# 变量
# ---------------------------------------------------------------------------

BOUND = 'bound'
FREE = 'free'

class Variable(Expr):
    """变量出现（既可作为绑定变量定义，也可作为自由/约束引用）。

    Parameters
    ----------
    name : str
        变量名，用于显示和匹配。
    kind : {'free', 'bound'}
        - ``'free'`` : 自由变量，可调用 ``assign()`` 赋值。
        - ``'bound'`` : 局部变量，不可赋值（尝试赋值会抛出 TypeError）。
    """

    def __init__(self, name: str, kind: str):
        if kind not in ('free', 'bound'):
            raise ValueError("kind must be 'free' or 'bound'")
        self.name = name
        self.kind = kind
        self.value: Optional[Expr] = None  # 仅自由变量可赋值

    def assign(self, value: Union[Expr, int, float]):
        """为自由变量赋予一个表达式或常量。"""
        if self.kind != 'free':
            raise TypeError(f"Cannot assign to bound variable '{self.name}'")
        if isinstance(value, (int, float)):
            value = Const(value)
        self.value = value

    def _reduce_step(self, env: Dict[str, Expr]) -> Optional[Expr]:
        """自由变量在环境中被替换（一步）。"""
        if self.kind == 'free' and self.name in env:
            return env[self.name]
        return None

    def _to_string(self, outer_prec: int) -> str:
        return self.name

    def _substitute(self, var_name: str, replacement: Expr) -> Expr:
        # 只要名字匹配就替换，不管 kind
        if self.name == var_name:
            return replacement
        return self

    def _free_vars(self) -> set:
        if self.kind == 'free':
            return {self.name}
        return set()

    def __repr__(self):
        return f"Variable('{self.name}', '{self.kind}')"

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, Variable):
            return self.name == other.name and self.kind == other.kind
        return False

    def __hash__(self):
        return hash(('Variable', self.name, self.kind))


# ---------------------------------------------------------------------------
# 抽象
# ---------------------------------------------------------------------------

class Lambda(Expr):
    """λ 抽象：``λ 变量. 体``。"""

    _prec = 2  # 抽象优先级较低（避免多余括号）

    def __init__(self, var: Variable, body: Expr):
        if var.kind != 'bound':
            raise TypeError(f"Lambda variable must be bound, got '{var.kind}'")
        self.var = var
        self.body = body

    # ------------------------------------------------------------------
    # 公共方法
    # ------------------------------------------------------------------
    def alpha(self, new_var: Variable) -> 'Lambda':
        """α 转换：将绑定变量重命名为 ``new_var``，避免捕获。

        若 ``new_var`` 的名称与体内自由变量冲突，会自动生成新名字并
        发出黄色警告。

        Parameters
        ----------
        new_var : Variable
            新变量，必须为 ``kind='bound'`` 类型。

        Returns
        -------
        Lambda
            重命名后的抽象。
        """
        if new_var.kind != 'bound':
            raise TypeError("New variable must be bound.")

        body_fv = self.body._free_vars()
        if new_var.name in body_fv:
            # 冲突：生成不冲突的名字
            fresh = fresh_var_name(new_var.name, body_fv)
            warn_yellow(
                f"Alpha: variable '{new_var.name}' would capture free occurrence. "
                f"Renamed to '{fresh}'."
            )
            new_var = Variable(fresh, 'bound')
        # 替换体内的旧变量
        new_body = self.body._substitute(self.var.name, new_var)
        return Lambda(new_var, new_body)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------
    def _reduce_step(self, env: Dict[str, Expr]) -> Optional[Expr]:
        """抽象本身不是 redex，但可以在体内归约。"""
        inner = self.body._reduce_step(env)
        if inner is not None:
            return Lambda(self.var, inner)
        return None

    def _to_string(self, outer_prec: int) -> str:
        # 抽象向右延伸，所以体不用括号（除非体内优先级更低）
        body_str = self.body._to_string(self._prec)
        s = f"λ{self.var.name}.{body_str}"
        if outer_prec > self._prec:
            return f"({s})"
        return s

    def _substitute(self, var_name: str, replacement: Expr) -> Expr:
        # 1. 若绑定变量与替换变量同名 → 无自由出现，原样返回
        if self.var.name == var_name:
            return self
        # 2. 若 replacement 中包含与绑定变量同名的自由变量 → 需要 α 转换
        replacement_fv = replacement._free_vars()
        if self.var.name in replacement_fv:
            # 生成一个新的、不与体内自由变量和 replacement 自由变量冲突的名字
            body_fv = self.body._free_vars()
            avoid = body_fv | replacement_fv
            fresh = fresh_var_name(self.var.name, avoid)
            # 对自身做 α 转换
            renamed = self.alpha(Variable(fresh, 'bound'))
            return renamed._substitute(var_name, replacement)
        # 3. 安全：替换体内
        new_body = self.body._substitute(var_name, replacement)
        if new_body is self.body:
            return self
        return Lambda(self.var, new_body)

    def _free_vars(self) -> set:
        return self.body._free_vars() - {self.var.name}

    def __repr__(self):
        return f"Lambda({self.var!r}, {self.body!r})"

    def __eq__(self, other):
        if isinstance(other, Lambda):
            return self.var == other.var and self.body == other.body
        return False

    def __hash__(self):
        return hash(('Lambda', self.var, self.body))


# ---------------------------------------------------------------------------
# 应用
# ---------------------------------------------------------------------------

class Apply(Expr):
    """函数应用：``(func arg)``。"""

    _prec = 3  # 应用优先级介于抽象和原子之间

    def __init__(self, func: Expr, arg: Expr):
        self.func = func
        self.arg = arg

    # ------------------------------------------------------------------
    def _reduce_step(self, env: Dict[str, Expr]) -> Optional[Expr]:
        """正常序：先尝试归约函数部分，然后 β 归约。"""
        # 如果函数本身是抽象 → β redex
        if isinstance(self.func, Lambda):
            return self._beta_reduce(self.func)
        # 否则尝试归约函数部分
        new_func = self.func._reduce_step(env)
        if new_func is not None:
            return Apply(new_func, self.arg)
        # 再尝试归约参数部分
        new_arg = self.arg._reduce_step(env)
        if new_arg is not None:
            return Apply(self.func, new_arg)
        return None

    def _beta_reduce(self, lam: Lambda) -> Expr:
        """执行一次 β 归约：把抽象体中的绑定变量替换为当前参数。"""
        return lam.body._substitute(lam.var.name, self.arg)

    def _to_string(self, outer_prec: int) -> str:
        func_str = self.func._to_string(self._prec)
        arg_str = self.arg._to_string(self._prec + 1)  # 应用左结合，右侧要略高
        s = f"{func_str} {arg_str}"
        if outer_prec > self._prec:
            return f"({s})"
        return s

    def _substitute(self, var_name: str, replacement: Expr) -> Expr:
        new_func = self.func._substitute(var_name, replacement)
        new_arg = self.arg._substitute(var_name, replacement)
        if new_func is self.func and new_arg is self.arg:
            return self
        return Apply(new_func, new_arg)

    def _free_vars(self) -> set:
        return self.func._free_vars() | self.arg._free_vars()

    def __repr__(self):
        return f"Apply({self.func!r}, {self.arg!r})"

    def __eq__(self, other):
        if isinstance(other, Apply):
            return self.func == other.func and self.arg == other.arg
        return False

    def __hash__(self):
        return hash(('Apply', self.func, self.arg))


# ---------------------------------------------------------------------------
# 构造器
# ---------------------------------------------------------------------------

def lam(var: Variable, body: Expr) -> Lambda:
    """创建 λ 抽象。

    Parameters
    ----------
    var : Variable
        必须为 ``kind='bound'`` 的变量对象。
    body : Expr
        函数体。

    Returns
    -------
    Lambda
    """
    if not isinstance(var, Variable):
        raise TypeError("var must be a Variable")
    if var.kind != 'bound':
        raise ValueError("Lambda variable must be 'bound'")
    return Lambda(var, body)


def let_lam(var: Variable, value: Expr, body: Expr) -> Apply:
    """let 绑定：``let var = value in body`` 编码为 ``(λvar. body) value``。

    Parameters
    ----------
    var : Variable
        局部变量，必须为 ``'bound'``。
    value : Expr
        绑定值，可以是任何表达式。
    body : Expr
        使用该变量的体。

    Returns
    -------
    Apply
        应用 ``(λvar. body) value``。
    """
    if not isinstance(var, Variable) or var.kind != 'bound':
        raise ValueError("let variable must be a bound Variable")
    return Apply(Lambda(var, body), value)