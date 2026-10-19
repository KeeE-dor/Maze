"""手写队列（B 同学 · 第 2 周）—— BFS 队列版的核心依赖。

先进先出 FIFO：enqueue 入队（尾部进）/ dequeue 出队（头部出）/ front 看队首 / is_empty。

⚠️ 千万别用 list.pop(0) 当队列——它是 O(n)（后面全部元素前移）。
两种合格的手写方案（二选一，答辩都有讲点）：
    1. 循环队列：定长数组 + head/tail 下标 + 取模回绕（经典，推荐）；
    2. 两栈拼队列：入队栈 + 出队栈互相倒，均摊 O(1)（经典面试题）。
包一层 collections.deque 也算能跑，但要能讲清 deque 为什么两头都是 O(1)
（分块双向链表）——建议还是手写循环队列，得分更稳。
"""
from __future__ import annotations


class Queue:
    def __init__(self, capacity: int = 1024):
        """循环队列方案：capacity 给个默认值，满了可以扩容（翻倍 + 搬迁）。

        TODO：准备好 _data / _head / _size（或 _tail）字段。
        """
        raise NotImplementedError("TODO 第 2 周")

    def __len__(self) -> int:
        raise NotImplementedError("TODO 第 2 周")

    def is_empty(self) -> bool:
        raise NotImplementedError("TODO 第 2 周")

    def enqueue(self, item) -> None:
        """TODO：item 入队尾；满时扩容或抛 IndexError（选一种，docstring 写明）。"""
        raise NotImplementedError("TODO 第 2 周")

    def dequeue(self):
        """TODO：弹出并返回队首元素；空队抛 IndexError。"""
        raise NotImplementedError("TODO 第 2 周")

    def front(self):
        """TODO：返回队首元素但不弹出；空队抛 IndexError。"""
        raise NotImplementedError("TODO 第 2 周")
