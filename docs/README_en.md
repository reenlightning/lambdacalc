<h1 align="center">lambdacalc</h1>
<p align="center"><a href="https://github.com/reenlightning/lambdacalc/blob/master/README.md">简体中文</a> | <a href="https://github.com/reenlightning/lambdacalc/blob/master/docs/README_en.md">English</a></p>

A lightweight DSL that embeds lambda calculus directly into Python, providing an object-oriented API for constructing, reducing, and evaluating λ expressions. Supports free variable assignment, α‑conversion (with automatic capture avoidance), β‑reduction, built‑in arithmetic operations, and lazy evaluation.
<hr>

## Quick Start

### Installation
#### Requirements

- Python 3.7+
- Dependency: [`colorama`](https://pypi.org/project/colorama/)

#### Installing via pip

```bash
pip install lambdacalc
```

#### Installing from source
Make sure you have [`git`](https://git-scm.com/install/windows) installed and correctly added to your system PATH.
```bash
git clone https://github.com/reenlightning/lambdacalc.git
cd lambdacalc
pip install .
```
### Example Code
```python
from lambdacalc import *

# 1. Create bound variables
x = Variable('x', 'bound')
y = Variable('y', 'bound')

# 2. Define the expression λx.λy.(x y) + 1
inner = lam(y, Add(Apply(x, y), Const(1)))
expr = lam(x, inner)

# 3. Create a free variable and assign a value to it
f = Variable('f', 'free')
f.assign(lam(Variable('a', 'bound'), Add(Variable('a', 'bound'), Const(1))))

# 4. Application and evaluation
app = expr.beta(f)          # (λx.λy.(x y)+1) (λa.a+1)
result = app.calculate([])  # Normal‑order reduction
print(result.building())    # λy. y + 2  (the normal form is still an abstraction)
```
<hr>

## Project Structure

```
lambdacalc/
├── __init__.py
├── _core.py
├── _builtins.py
└── _utils.py
```

<hr>

## Core API

### Variables

- `Variable(name: str, kind: str)`  
  Creates a variable. `kind` can be `'free'` (free variable, can be assigned) or `'bound'` (bound variable, cannot be assigned).
- `var.assign(value: Expr | int | float)`  
  Assigns a value to a free variable. Numbers are automatically wrapped as `Const`.

### Constructing Expressions

- `lam(var: Variable, body: Expr) -> Lambda`  
  Returns a `λ var. body` abstraction. `var` must be of `'bound'` kind.
- `let_lam(var: Variable, value: Expr, body: Expr) -> Apply`  
  let‑binding, equivalent to `(λvar. body) value`. `var` must be `'bound'`.

### Expression Methods

All expression objects (subclasses of `Expr`) support the following methods:

- `expr.beta(arg: Expr) -> Apply`  
  Constructs an application expression `(expr arg)` **without performing reduction**.
- `expr.calculate(env: List[Variable]) -> int | float | Expr`  
  Uses normal‑order (lazy) evaluation to reduce the expression to its normal form.  
  `env` is a list of free variable objects that have already been assigned; their values are substituted during evaluation.  
  Returns: a Python number if the normal form is a numeric constant, otherwise an expression object.
- `expr.building() -> str`  
  Returns a human‑readable string using `λ`, omitting unnecessary parentheses according to associativity rules.
- `lambda_expr.alpha(new_var: Variable) -> Lambda`  
  α‑conversion: renames the bound variable of the abstraction to `new_var` (must be `'bound'`).  
  Automatically detects variable capture: if the new name conflicts with free variables in the body, a fresh name is generated and a yellow `[Warning]` is printed.

### Built‑in Arithmetic

- `Add(left, right)`, `Sub(left, right)`, `Mult(left, right)`, `Div(left, right)`  
  Binary arithmetic nodes. When `calculate` reduces both sides to `Const` values, they are automatically folded into a numeric constant.

<hr>

## Behavioral Details

### Reduction Strategy
`calculate` uses **normal order** (leftmost outermost redex first). This is a safe evaluation order: if an expression has a β‑normal form, it will always be found, and the evaluator will never get stuck in an unnecessary infinite loop.

### Handling of Free Variables
- `calculate(env)` only substitutes those free variables in the `env` list that have been assigned a value; other free variables remain unchanged.
- During reduction, if a free variable is encountered that is not present in the environment, evaluation of that branch stops.

### Capture Avoidance (α‑conversion)
During β‑reduction or substitution, if the expression being substituted contains a free variable with the same name as a bound variable of an abstraction, the bound variable is **automatically renamed** to avoid accidental capture, and a yellow `[Warning]` is printed.  
Example:
```python
x = Variable('x', 'bound'); y = Variable('y', 'free')
expr = lam(x, lam(Variable('y', 'bound'), Apply(x, Variable('y', 'bound'))))
# Application: (λx.λy.x y) y
app = expr.beta(y)
# The reduction triggers a warning and produces something like λy1.y y1
```

### Immutability
All expression objects are immutable. Every reduction, substitution, and α‑conversion method returns a **new expression object**; the original remains unchanged.

<hr>

## More Examples

### Basic Arithmetic and let Binding
```python
x = Variable('x', 'bound')
let_expr = let_lam(x, Const(10), Mult(x, Const(3)))  # let x = 10 in x * 3
print(let_expr.building())       # (λx. x * 3) 10
print(let_expr.calculate([]))    # 30
```

### Church Booleans and Conditionals (Pure Lambda Calculus)
```python
# true = λx.λy.x ; false = λx.λy.y
true = lam(Variable('x', 'bound'), lam(Variable('y', 'bound'), Variable('x', 'bound')))
false = lam(Variable('x', 'bound'), lam(Variable('y', 'bound'), Variable('y', 'bound')))
# Use a free variable if_then_else to implement conditionals, omitted here
```

### Higher‑Order Function: `twice`
```python
f = Variable('f', 'bound'); x = Variable('x', 'bound')
twice = lam(f, lam(x, Apply(f, Apply(f, x))))
inc = lam(Variable('z', 'bound'), Add(Variable('z', 'bound'), Const(1)))
step1 = twice.beta(inc)        # (λf.λx.f(f x)) inc
step2 = step1.beta(Const(5))
print(step2.calculate([]))     # 7
```

To publish to PyPI or a private index, refer to the metadata in `pyproject.toml` and use `twine` upload.

<hr>

## License

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