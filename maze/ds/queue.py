"""手写队列（B 同学 · 第 2 周）—— BFS 队列版的核心依赖。

先进先出 FIFO：enqueue 入队（尾部进）/ dequeue 出队（头部出）/ front 看队首 / is_empty。

⚠️ 千万别用 list.pop(0) 当队列——它是 O(n)（后面全部元素前移）。
两种合格的手写方案（二选一，答辩都有讲点）：
    1. 循环队列：定长数组 + head/tail 下标 + 取模回绕（经典，推荐）；
    2. 两栈拼队列：入队栈 + 出队栈互相倒，均摊 O(1)（经典面试题）。
包一层 collections.deque 也算能跑，但要能讲清 deque 为什么两头都是 O(1)
（分块双向链表）——建议还是手写循环队列，得分更稳。

本实现采用循环队列：定长数组 _data + _head（队首下标）+ _size（元素个数），
不维护 tail（tail = (_head + _size) % cap 推导得出，两个指针容易打架）。
满了翻倍扩容：新建数组，从 head 开始按出队顺序搬迁（否则绕环顺序会被打乱）。
"""
from __future__ import annotations


class Queue:
    def __init__(self, capacity: int = 1024):
        """循环队列方案：capacity 给个默认值，满了翻倍扩容 + 搬迁。O(capacity)。"""
        if capacity < 1:
            raise ValueError("capacity 至少为 1")
        self._data: list = [None] * capacity
        self._head: int = 0   # 队首元素所在下标
        self._size: int = 0   # 当前元素个数；满即 _size == len(_data)

    def __len__(self) -> int:
        """返回元素个数。O(1)：直接读 _size。"""
        return self._size

    def is_empty(self) -> bool:
        """是否为空。O(1)。"""
        return self._size == 0

    def enqueue(self, item) -> None:
        """item 入队尾。均摊 O(1)：写入 (_head + _size) % cap 处；
        偶尔满员时翻倍扩容 + 搬迁（O(n)），均摊后仍是常数。"""
        if self._size == len(self._data):
            self._grow()
        self._data[(self._head + self._size) % len(self._data)] = item
        self._size += 1

    def dequeue(self):
        """弹出并返回队首元素；空队抛 IndexError。O(1)：只移动 _head，不搬元素。"""
        if self._size == 0:
            raise IndexError("dequeue from empty queue")
        item = self._data[self._head]
        self._data[self._head] = None  # 释放引用，避免悬挂对象
        self._head = (self._head + 1) % len(self._data)
        self._size -= 1
        return item

    def front(self):
        """返回队首元素但不弹出；空队抛 IndexError。O(1)。"""
        if self._size == 0:
            raise IndexError("front from empty queue")
        return self._data[self._head]

    def _grow(self) -> None:
        """容量翻倍，从 _head 起按出队顺序搬到新数组头部。O(n)。"""
        old = self._data
        cap = len(old)
        self._data = [None] * (cap * 2)
        for i in range(self._size):
            self._data[i] = old[(self._head + i) % cap]
        self._head = 0
