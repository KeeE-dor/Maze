"""基于 list 的 LIFO 栈，空栈读取或弹出时抛出 IndexError。"""
from __future__ import annotations


class Stack:
    def __init__(self):
        self._items: list = []

    def __len__(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return not self._items

    def push(self, item) -> None:
        """压入栈顶。均摊 O(1)。"""
        self._items.append(item)

    def pop(self):
        """弹出并返回栈顶元素；空栈抛 IndexError。均摊 O(1)。"""
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self):
        """查看栈顶元素但不弹出；空栈抛 IndexError。O(1)。"""
        if not self._items:
            raise IndexError("peek from empty stack")
        return self._items[-1]
