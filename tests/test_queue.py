"""Queue 单元测试，重点验证循环队列绕环与扩容。"""
import pytest

from maze.ds.queue import Queue


def test_fifo_order():
    q = Queue()
    for i in range(5):
        q.enqueue(i)
    assert [q.dequeue() for _ in range(5)] == [0, 1, 2, 3, 4]


def test_front_does_not_remove():
    q = Queue()
    q.enqueue("a")
    q.enqueue("b")
    assert q.front() == "a"
    assert len(q) == 2 and not q.is_empty()


def test_dequeue_and_front_on_empty_raise():
    q = Queue()
    with pytest.raises(IndexError):
        q.dequeue()
    with pytest.raises(IndexError):
        q.front()


def test_len_and_is_empty_track_state():
    q = Queue()
    assert len(q) == 0 and q.is_empty()
    q.enqueue(1)
    assert len(q) == 1 and not q.is_empty()
    q.dequeue()
    assert len(q) == 0 and q.is_empty()


def test_wraparound():
    q = Queue(capacity=8)
    for i in range(8):
        q.enqueue(i)
    for i in range(4):
        assert q.dequeue() == i
    for i in range(8, 14):
        q.enqueue(i)
    assert len(q) == 10
    assert [q.dequeue() for _ in range(10)] == [4, 5, 6, 7, 8, 9, 10, 11, 12, 13]


def test_grow_preserves_order():
    q = Queue(capacity=4)
    for i in range(7):
        q.enqueue(i)
    assert len(q) == 7
    assert [q.dequeue() for _ in range(7)] == [0, 1, 2, 3, 4, 5, 6]


def test_interleaved_grow_and_wraparound():
    """绕环后再触发扩容，确保搬迁保持先进先出顺序。"""
    q = Queue(capacity=4)
    for i in range(3):
        q.enqueue(i)
    assert q.dequeue() == 0
    for i in range(3, 6):
        q.enqueue(i)
    assert [q.dequeue() for _ in range(5)] == [1, 2, 3, 4, 5]
