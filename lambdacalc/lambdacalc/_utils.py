"""
辅助工具：黄色警告输出、新变量名生成。
"""

import colorama

# 初始化 colorama（跨平台兼容）
colorama.init(autoreset=True)


def warn_yellow(msg: str) -> None:
    """以黄色文本在 stderr 输出警告信息。

    Parameters
    ----------
    msg : str
        警告内容。
    """
    print(colorama.Fore.YELLOW + f"[Warning] {msg}", flush=True)


def fresh_var_name(base: str, avoid: set) -> str:
    """生成一个不在 ``avoid`` 集合中的新变量名。

    策略：在 ``base`` 后追加数字后缀，直到不冲突。

    Parameters
    ----------
    base : str
        基础变量名。
    avoid : set of str
        需要避开的变量名字符串集合。

    Returns
    -------
    str
        生成的新名字。
    """
    if base not in avoid:
        return base
    i = 1
    while True:
        candidate = f"{base}{i}"
        if candidate not in avoid:
            return candidate
        i += 1