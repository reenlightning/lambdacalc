"""
示例：λ 演算 DSL 用法演示
"""
from ._core import *
from ._builtins import *


if __name__ == "__main__":
    print("=== 基础抽象 ===")
    x = Variable('x', BOUND)
    identity = lam(x, x)
    print("恒等函数:", identity.building())  # λx.x

    print("\n=== 自由变量赋值与求值 ===")
    a = Variable('a', FREE)
    a.assign(5)
    expr1 = lam(Variable('y', BOUND), Add(a, Variable('y', BOUND)))
    print("表达式:", expr1.building())  # λy. a + y
    # 求值，a 被替换为 5
    res1 = expr1.calculate([a])
    print("求值结果:", res1)  # 数字还是表达式？由于归约后是 λy. 5 + y，无法再归约，返回 Expr
    print("结果 building:", res1.building() if not isinstance(res1, (int, float)) else res1)

    print("\n=== β 应用与归约 ===")
    f = lam(Variable('z', BOUND), Mult(Variable('z', BOUND), Const(2)))  # λz. z * 2
    app = f.beta(Const(3))  # (λz. z*2) 3
    print("应用:", app.building())
    result = app.calculate([])
    print("归约结果:", result)  # 6 (int)

    print("\n=== let 绑定 ===")
    # let x = 10 in x * 3
    x_let = Variable('x', BOUND)
    let_expr = let_lam(x_let, Const(10), Mult(x_let, Const(3)))
    print("let 表达式:", let_expr.building())  # (λx. x * 3) 10
    val = let_expr.calculate([])
    print("求值:", val)  # 30

    print("\n=== 捕获警告与 α 转换 ===")
    # 构造 (λx.λy. x y) y，若直接替换 y 会发生捕获
    xx = Variable('x', BOUND)
    yy = Variable('y', BOUND)
    body = lam(yy, Apply(xx, yy))  # λy. x y
    outer = lam(xx, body)  # λx.λy. x y
    free_y = Variable('y', FREE)
    # 应用 (λx.λy. x y) y
    app2 = outer.beta(free_y)
    # 此时 building 会显示什么？ 由于 free_y 是表达式，会显示为 y
    print("应用前:", outer.building())
    print("应用后:", app2.building())  # (λx.λy. x y) y
    # 求值：应触发捕获避免
    res2 = app2.calculate([])
    print("归约结果:", res2.building())  # 应显示 λy'. y y' 之类，并有黄色警告

    print("\n=== 复杂计算 ===")
    # (λf.λx. f (f x)) (λz. z + 1) 5  即 twice inc 5 => 7
    f_var = Variable('f', BOUND)
    x_var = Variable('x', BOUND)
    twice = lam(f_var, lam(x_var, Apply(f_var, Apply(f_var, x_var))))
    inc = lam(Variable('z', BOUND), Add(Variable('z', BOUND), Const(1)))
    step1 = twice.beta(inc)  # (λf.λx. f (f x)) inc
    step2 = step1.beta(Const(5))  # 应用 5
    final = step2.calculate([])
    print("twice inc 5 =", final)  # 7