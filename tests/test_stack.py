"""Stack 单元测试。"""
import pytest

from maze.ds.stack import Stack


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
