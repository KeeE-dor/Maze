"""基于定长数组实现的 FIFO 循环队列，满时按出队顺序翻倍扩容。"""
from __future__ import annotations


class Queue:
    def __init__(self, capacity: int = 1024):
        """初始化指定初始容量的循环队列。O(capacity)。"""
        if capacity < 1:
            raise ValueError("capacity 至少为 1")
        self._data: list = [None] * capacity
        self._head: int = 0
        self._size: int = 0

    def __len__(self) -> int:
        return self._size

    def is_empty(self) -> bool:
        return self._size == 0

    def enqueue(self, item) -> None:
        """入队尾；队列满时自动翻倍扩容。均摊 O(1)。"""
        if self._size == len(self._data):
            self._grow()
        self._data[(self._head + self._size) % len(self._data)] = item
        self._size += 1

    def dequeue(self):
        """出队首并返回元素；空队抛 IndexError。O(1)。"""
        if self._size == 0:
            raise IndexError("dequeue from empty queue")
        item = self._data[self._head]
        self._data[self._head] = None  # 避免引用滞留
        self._head = (self._head + 1) % len(self._data)
        self._size -= 1
        return item

    def front(self):
        """查看队首元素但不出队；空队抛 IndexError。O(1)。"""
        if self._size == 0:
            raise IndexError("front from empty queue")
        return self._data[self._head]

    def _grow(self) -> None:
        """容量翻倍，从 _head 起按出队顺序搬迁元素。O(n)。"""
        old = self._data
        cap = len(old)
        self._data = [None] * (cap * 2)
        for i in range(self._size):
            self._data[i] = old[(self._head + i) % cap]
        self._head = 0
