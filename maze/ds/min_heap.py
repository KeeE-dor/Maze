from __future__ import annotations


import heapq


class MinHeap:

  def __init__(self):
    self._items: list = []

  def __len__(self) -> int:
    return len(self._items)

  def is_empty(self) -> bool:
    return not self._items

  def push(self, item) -> None:
    heapq.heappush(self._items, item)

  def pop(self):
    if not self._items:
      raise IndexError("pop from empty heap")
    return heapq.heappop(self._items)

  def peek(self):
    if not self._items:
      raise IndexError("peek from empty heap")
    return self._items[0]