"""手写栈（B 同学 · 第 2 周）—— DFS 非递归版的核心依赖。

后进先出 LIFO。对外只暴露：push 压栈 / pop 弹栈并返回 / peek 看栈顶 / is_empty / __len__。
内部用 Python list 即可（append 和尾部 pop 都是 O(1)）。

课程要求手写的意义不在"造轮子"，而在你要明确边界行为：空栈 pop / peek 怎么办
（这里约定抛 IndexError）、什么时候栈会无限增长（DFS 非递归版忘标 visited 时）。
答辩会问"你的栈和 list 有什么区别"——答：接口收敛 + 边界明确。
"""
from __future__ import annotations


class Stack:
    def __init__(self):
        self._items: list = []

    def __len__(self) -> int:
        """TODO：返回元素个数。"""
        raise NotImplementedError("TODO 第 2 周")

    def is_empty(self) -> bool:
        """TODO：是否为空。"""
        raise NotImplementedError("TODO 第 2 周")

    def push(self, item) -> None:
        """TODO：压入栈顶。"""
        raise NotImplementedError("TODO 第 2 周")

    def pop(self):
        """弹出并返回栈顶元素；空栈抛 IndexError。TODO。"""
        raise NotImplementedError("TODO 第 2 周")

    def peek(self):
        """返回栈顶元素但不弹出；空栈抛 IndexError。TODO。"""
        raise NotImplementedError("TODO 第 2 周")
