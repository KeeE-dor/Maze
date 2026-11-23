"""MinHeap 单元测试。"""
from __future__ import annotations

import heapq
from pathlib import Path
import random

import pytest

from maze.ds.min_heap import MinHeap


def test_min_order():
    h = MinHeap()
    for val in [5, 1, 9, -2, 3, 3, 0]:
        h.push(val)
    popped = [h.pop() for _ in range(len(h))]
    assert popped == [-2, 0, 1, 3, 3, 5, 9]
    assert h.is_empty()


def test_tuple_weights_for_generators():
    h = MinHeap()
    edges = [(0.7, 0, 1, 0, 2), (0.1, 1, 0, 2, 0), (0.4, 0, 0, 0, 1)]
    for e in edges:
        h.push(e)
    assert h.pop()[0] == 0.1
    assert h.pop()[0] == 0.4
    assert h.pop()[0] == 0.7


def test_peek_does_not_remove():
    h = MinHeap()
    h.push(42)
    h.push(10)
    assert h.peek() == 10
    assert len(h) == 2
    assert not h.is_empty()


def test_empty_pop_and_peek_raise():
    h = MinHeap()
    with pytest.raises(IndexError):
        h.pop()
    with pytest.raises(IndexError):
        h.peek()


def test_single_element_push_pop():
    h = MinHeap()
    h.push(7)
    assert h.pop() == 7
    assert h.is_empty()
    assert len(h) == 0


def test_matches_heapq_random_fuzz():
    """随机混合压入与弹出，与标准库 heapq 结果对拍。"""
    rng = random.Random(2026)
    h = MinHeap()
    ref: list[int] = []

    for _ in range(1000):
        op = rng.random()
        if op < 0.6 or not ref:
            val = rng.randint(-500, 500)
            h.push(val)
            heapq.heappush(ref, val)
        else:
            assert h.peek() == ref[0]
            assert h.pop() == heapq.heappop(ref)
        assert len(h) == len(ref)

    while ref:
        assert h.pop() == heapq.heappop(ref)
    assert h.is_empty()


def test_no_stdlib_heapq_used_in_implementation():
    src = (Path(__file__).resolve().parent.parent / "maze" / "ds" / "min_heap.py").read_text(
        encoding="utf-8"
    )
    assert "heapq" not in src
