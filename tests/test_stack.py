"""Stack 的单元测试示范（B 同学第 2 周实现 stack.py 后，删除顶部 skip 行跑绿）。

写测试的三段套路（后面的 Queue/MinHeap/UnionFind 照此自己写）：
    1. 正常流程：push 一串、pop 出来验证 LIFO 顺序
    2. 边界：空栈 pop/peek 的异常行为
    3. 性质：peek 不弹出、len 随动
"""
import pytest

from maze.ds.stack import Stack

pytestmark = pytest.mark.skip(reason="待第 2 周实现 Stack 后删除本行")


def test_lifo_order():
    s = Stack()
    s.push(1)
    s.push(2)
    s.push(3)
    assert s.pop() == 3
    assert s.pop() == 2
    assert s.pop() == 1


def test_peek_does_not_remove():
    s = Stack()
    s.push("a")
    assert s.peek() == "a"
    assert not s.is_empty()
    assert len(s) == 1


def test_pop_and_peek_on_empty_raise():
    s = Stack()
    with pytest.raises(IndexError):
        s.pop()
    with pytest.raises(IndexError):
        s.peek()


def test_len_tracks_pushes():
    s = Stack()
    assert len(s) == 0 and s.is_empty()
    for i in range(5):
        s.push(i)
    assert len(s) == 5
