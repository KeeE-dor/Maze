"""手写最小堆 / 优先队列（A 同学 · 第 2–4 周）—— Kruskal / Prim 取"最小随机权边"用。

二叉堆 = 用数组存的完全二叉树：
    i 的左孩子 2i+1，右孩子 2i+2，父节点 (i-1)//2
    push(item)  O(log n)：追加到数组末尾，向上与父比较、比父小就交换（sift-up 上浮）
    pop()       O(log n)：取走堆顶，把末尾元素放到顶，向下与【较小的】孩子交换（sift-down 下沉）
    peek()      O(1)：看堆顶不弹出

存迷宫边时建议 item 用元组 (weight, r1, c1, r2, c2)：
Python 元组比较是字典序，权重相同时自动比后面的字段，出边顺序稳定、结果可复现。

答辩考点：为什么用堆而不是每次 sort？—— 边只需要"逐条取出最小"，
sort 是一次性 O(n log n) 但每次取完不动，堆支持动态插入（Prim 的 frontier 边
是边生长边加入的），单次取最小只要 O(log n)。
"""
from __future__ import annotations


class MinHeap:
    def __init__(self):
        self._items: list = []

    def __len__(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return not self._items

    def push(self, item) -> None:
        """TODO：append 到 _items 末尾，然后 _sift_up(len(self._items) - 1)。"""
        raise NotImplementedError("TODO：push + 上浮")

    def pop(self):
        """弹出并返回最小元素；空堆抛 IndexError。

        TODO：标准三步——记下堆顶 -> 把末尾元素放到 index 0 -> _sift_down(0)。
        注意只有 1 个元素时直接弹出即可。
        """
        raise NotImplementedError("TODO：pop + 下沉")

    def peek(self):
        """返回最小元素但不弹出；空堆抛 IndexError。（已给实现）"""
        if not self._items:
            raise IndexError("peek from empty heap")
        return self._items[0]

    # TODO：补两个私有辅助方法
    # def _sift_up(self, i):   与父节点比，小于父就换上去，直到到顶或不再小于
    # def _sift_down(self, i): 与较小的那个孩子比，大于它就换下去，直到无孩子或不再大于
