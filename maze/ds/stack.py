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
        """返回元素个数。O(1)：list 自带长度。"""
        return len(self._items)

    def is_empty(self) -> bool:
        """是否为空。O(1)。"""
        return not self._items

    def push(self, item) -> None:
        """压入栈顶。均摊 O(1)：list.append 尾部追加，偶尔触发的扩容代价
        均摊到每次 append 后仍是常数。"""
        self._items.append(item)

    def pop(self):
        """弹出并返回栈顶元素；空栈抛 IndexError。均摊 O(1)：尾部删除。"""
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self):
        """返回栈顶元素但不弹出；空栈抛 IndexError。O(1)。"""
        if not self._items:
            raise IndexError("peek from empty stack")
        return self._items[-1]
