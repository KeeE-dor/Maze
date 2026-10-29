"""Queue 的单元测试（B 同学 · 第 2 周）—— 照 test_stack.py 的三段套路写。

重点盯循环队列最容易翻车的两处：
    1. 绕环：下标取模回绕后顺序是否还对；
    2. 扩容：翻倍搬迁必须从 head 起按出队顺序搬，否则老元素顺序会乱。
"""
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
    """容量 8：入 8 出 4 再入 6 —— 后 6 个里前 4 个落在新绕环的位置上。"""
    q = Queue(capacity=8)
    for i in range(8):
        q.enqueue(i)
    for i in range(4):
        assert q.dequeue() == i          # 先出的还是最老的 0..3
    for i in range(8, 14):               # 6 个新元素：4 个绕回数组头部
        q.enqueue(i)
    assert len(q) == 10
    assert [q.dequeue() for _ in range(10)] == [4, 5, 6, 7, 8, 9, 10, 11, 12, 13]


def test_grow_preserves_order():
    """容量 4：先填满再继续入队触发翻倍扩容，出队顺序必须保持 FIFO。"""
    q = Queue(capacity=4)
    for i in range(7):                   # 7 > 4，必然扩容
        q.enqueue(i)
    assert len(q) == 7
    assert [q.dequeue() for _ in range(7)] == [0, 1, 2, 3, 4, 5, 6]


def test_interleaved_grow_and_wraparound():
    """绕环状态下触发扩容：搬迁从 head 起按出队顺序，顺序不能乱。"""
    q = Queue(capacity=4)
    for i in range(3):                   # data: 0 1 2 _
        q.enqueue(i)
    assert q.dequeue() == 0              # head 移到 1
    for i in range(3, 6):                # 3 落在尾部空位，4 5 绕回头部并触发扩容
        q.enqueue(i)
    assert [q.dequeue() for _ in range(5)] == [1, 2, 3, 4, 5]
