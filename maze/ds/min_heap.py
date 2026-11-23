"""基于 0 下标数组实现的二叉小顶堆，堆顶恒为最小元素。"""
from __future__ import annotations


class MinHeap:
    def __init__(self) -> None:
        self._items: list = []

    def __len__(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return not self._items

    def push(self, item) -> None:
        """插入元素并上浮恢复堆序。均摊 O(log n)。"""
        self._items.append(item)
        self._sift_up(len(self._items) - 1)

    def pop(self):
        """弹出并返回堆顶最小元素；空堆抛 IndexError。O(log n)。"""
        if not self._items:
            raise IndexError("pop from empty heap")
        top = self._items[0]
        last = self._items.pop()
        if self._items:
            self._items[0] = last
            self._sift_down(0)
        return top

    def peek(self):
        """查看堆顶元素但不弹出；空堆抛 IndexError。O(1)。"""
        if not self._items:
            raise IndexError("peek from empty heap")
        return self._items[0]

    def _sift_up(self, idx: int) -> None:
        """将 idx 处元素向上调整直到满足小顶堆性质。O(log n)。"""
        while idx > 0:
            parent = (idx - 1) // 2
            if self._items[idx] < self._items[parent]:
                self._items[idx], self._items[parent] = self._items[parent], self._items[idx]
                idx = parent
            else:
                break

    def _sift_down(self, idx: int) -> None:
        """将 idx 处元素向下与较小子节点交换直到满足小顶堆性质。O(log n)。"""
        n = len(self._items)
        while True:
            left = 2 * idx + 1
            right = left + 1
            smallest = idx
            if left < n and self._items[left] < self._items[smallest]:
                smallest = left
            if right < n and self._items[right] < self._items[smallest]:
                smallest = right
            if smallest == idx:
                break
            self._items[idx], self._items[smallest] = self._items[smallest], self._items[idx]
            idx = smallest
