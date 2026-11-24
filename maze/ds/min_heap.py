"""基于 0 下标数组实现的二叉小顶堆（最小堆）。

在数组中的下标规律（假设当前节点下标为 i）：
- 父节点下标: (i - 1) // 2
- 左孩子下标: 2 * i + 1
- 右孩子下标: 2 * i + 2

性质：任意节点的值都 <= 它左右孩子的值，因此根节点 _items[0] 永远是最小的元素。
"""
from __future__ import annotations


class MinHeap:
    def __init__(self) -> None:
        # 用一个普通 Python 列表按完全二叉树层序存储所有元素
        self._items: list = []

    def __len__(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return not self._items

    def push(self, item) -> None:
        """插入元素并上浮恢复堆序。均摊时间复杂度 O(log n)。"""
        # 1. 先把新元素放到数组末尾（相当于完全二叉树的最底层最右端）
        self._items.append(item)
        # 2. 从末尾位置开始向上调整（上浮），直到比父节点大或到达堆顶
        self._sift_up(len(self._items) - 1)

    def pop(self):
        """弹出并返回堆顶最小元素；空堆抛 IndexError。时间复杂度 O(log n)。"""
        if not self._items:
            raise IndexError("pop from empty heap")
        # 1. 取出堆顶最小值，准备最后返回
        top = self._items[0]
        # 2. 弹出数组最后一个元素，准备用它填补堆顶空位（避免直接删除头部导致 O(n) 搬移）
        last = self._items.pop()
        # 3. 如果弹出后堆里还有元素，就把原末尾元素放到堆顶，再向下调整恢复堆序
        if self._items:
            self._items[0] = last
            self._sift_down(0)
        return top

    def peek(self):
        """查看堆顶最小元素但不弹出；空堆抛 IndexError。时间复杂度 O(1)。"""
        if not self._items:
            raise IndexError("peek from empty heap")
        return self._items[0]

    def _sift_up(self, idx: int) -> None:
        """上浮操作：把 idx 位置的元素不断与父节点比较，若更小就交换上去。O(log n)。"""
        while idx > 0:
            parent = (idx - 1) // 2
            # 如果当前节点比父节点小，说明违反了小顶堆性质，交换两者位置
            if self._items[idx] < self._items[parent]:
                self._items[idx], self._items[parent] = self._items[parent], self._items[idx]
                idx = parent  # 继续往上检查
            else:
                # 已经比父节点大或相等，满足小顶堆性质，可以提前结束
                break

    def _sift_down(self, idx: int) -> None:
        """下沉操作：把 idx 位置的元素不断与较小的孩子交换，直到它小于等于两个孩子。O(log n)。"""
        n = len(self._items)
        while True:
            left = 2 * idx + 1
            right = left + 1
            # 先假设当前节点就是三者（自己、左孩子、右孩子）中最小的
            smallest = idx
            # 若左孩子存在且更小，更新最小者下标
            if left < n and self._items[left] < self._items[smallest]:
                smallest = left
            # 若右孩子存在且比当前记录的最小者还小，更新最小者下标
            if right < n and self._items[right] < self._items[smallest]:
                smallest = right
            # 如果当前节点已经是最小的，说明堆序已恢复，结束循环
            if smallest == idx:
                break
            # 否则与较小的那个孩子交换，然后从孩子的位置继续往下沉
            self._items[idx], self._items[smallest] = self._items[smallest], self._items[idx]
            idx = smallest
