<h1 align="center">lambdacalc</h1>

一个将 λ 演算直接嵌入 Python 的轻量级 DSL，提供面向对象的 API 来构造、归约和求值 λ 表达式。支持自由变量赋值、α 转换（自动捕获避免）、β 归约、内置算术运算以及惰性求值。
<hr>

## 快速开始

### 安装
#### 要求

- Python 3.7+
- 依赖 [`colorama`](https://pypi.org/project/colorama/)

#### 通过 pip 安装

```bash
pip install lambdacalc
```

#### 从源码安装
请事先确认您已安装[`git`](https://git-scm.com/install/windows)，并确定已经将其正确地添加至系统PATH环境变量中。
```bash
git clone https://github.com/reenlightning/lambdacalc.git
cd lambdacalc
pip install .
```
### 示例代码
```python
from lambdacalc import *

# 1. 创建绑定变量
x = Variable('x', 'bound')
y = Variable('y', 'bound')

# 2. 定义表达式 λx.λy.(x y) + 1
inner = lam(y, Add(Apply(x, y), Const(1)))
expr = lam(x, inner)

# 3. 创建自由变量并赋值
f = Variable('f', 'free')
f.assign(lam(Variable('a', 'bound'), Add(Variable('a', 'bound'), Const(1))))

# 4. 应用与求值
app = expr.beta(f)          # (λx.λy.(x y)+1) (λa.a+1)
result = app.calculate([])  # 正常序归约
print(result.building())    # λy. y + 2 （范式依然是抽象）
```
<hr>

## 项目结构

```
lambdacalc/
├── __init__.py
├── _core.py
├── _builtins.py
└── _utils.py
```

<hr>

## 核心 API

### 变量

- `Variable(name: str, kind: str)`  
  创建一个变量。`kind` 可选 `'free'`（自由变量，可赋值）或 `'bound'`（局部变量，不可赋值）。
- `var.assign(value: Expr | int | float)`  
  为自由变量赋值。数字会自动包装为 `Const`。

### 构造表达式

- `lam(var: Variable, body: Expr) -> Lambda`  
  返回 `λ var. body` 抽象。`var` 必须是 `'bound'` 类型。
- `let_lam(var: Variable, value: Expr, body: Expr) -> Apply`  
  let 绑定，等价于 `(λvar. body) value`。`var` 必须是 `'bound'`。

### 表达式方法

所有表达式对象（`Expr` 子类）都支持以下方法：

- `expr.beta(arg: Expr) -> Apply`  
  构造应用表达式 `(expr arg)`，**不执行归约**。
- `expr.calculate(env: List[Variable]) -> int | float | Expr`  
  使用正常序（惰性求值）将表达式归约到范式。  
  `env` 为一组已赋值的自由变量对象，求值时会对它们进行代入。  
  返回：若范式为数字常量，则返回 Python 数值；否则返回表达式对象。
- `expr.building() -> str`  
  输出易读的字符串，使用 `λ`，按结合性规则省略多余括号。
- `lambda_expr.alpha(new_var: Variable) -> Lambda`  
  α 转换，将抽象绑定变量重命名为 `new_var`（必须是 `'bound'` 类型）。  
  自动检测变量捕获：若新名与体内自由变量冲突，会生成新名字并通过黄色 `[Warning]` 提示。

### 内建算术

- `Add(left, right)`、`Sub(left, right)`、`Mult(left, right)`、`Div(left, right)`  
  二元算术节点。当 `calculate` 归约到两侧都是 `Const` 时会自动折叠为数字常量。

<hr>

## 行为细节

### 归约策略
`calculate` 采用**正常序**（最左最外 redex 优先）。这是一个安全的求值顺序：只要表达式存在 β-范式，就一定能得到它，不会陷入不必要的无限循环。

### 自由变量的处理
- `calculate(env)` 只会替换 `env` 列表中那些已赋值的自由变量；其他自由变量保持原样。
- 归约过程中遇到的自由变量若不在环境中，则停止该分支的归约。

### 捕获避免（α 转换）
执行 β 归约或 `_substitute` 时，如果代入的表达式包含与抽象绑定变量同名的自由变量，系统会**自动对绑定变量进行重命名**以避免意外捕获，同时打印黄色 `[Warning]`。  
例如：
```python
x = Variable('x', 'bound'); y = Variable('y', 'free')
expr = lam(x, lam(Variable('y', 'bound'), Apply(x, Variable('y', 'bound'))))
# 应用 (λx.λy.x y) y
app = expr.beta(y)
# 归约会触发警告，并生成类似 λy1.y y1 的表达式
```

### 不可变性
所有表达式对象是不可变的。所有归约、替换、α 转换等方法均返回**新的表达式对象**，原始对象保持不变。

<hr>

## 更多示例

### 基础算术与 let 绑定
```python
x = Variable('x', 'bound')
let_expr = let_lam(x, Const(10), Mult(x, Const(3)))  # let x = 10 in x * 3
print(let_expr.building())       # (λx. x * 3) 10
print(let_expr.calculate([]))    # 30
```

### 邱奇布尔与条件（纯 λ 演算）
```python
# true = λx.λy.x ; false = λx.λy.y
true = lam(Variable('x', 'bound'), lam(Variable('y', 'bound'), Variable('x', 'bound')))
false = lam(Variable('x', 'bound'), lam(Variable('y', 'bound'), Variable('y', 'bound')))
# 使用自由变量 if_then_else 实现条件，这里略
```

### 高阶函数：twice
```python
f = Variable('f', 'bound'); x = Variable('x', 'bound')
twice = lam(f, lam(x, Apply(f, Apply(f, x))))
inc = lam(Variable('z', 'bound'), Add(Variable('z', 'bound'), Const(1)))
step1 = twice.beta(inc)        # (λf.λx.f(f x)) inc
step2 = step1.beta(Const(5))
print(step2.calculate([]))     # 7
```


发布到 PyPI 或私有索引请参考 `pyproject.toml` 中的元数据，使用 `twine` 上传。

<hr>

## 许可证

MIT License

Copyright (c) 2026 reenlightning

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


