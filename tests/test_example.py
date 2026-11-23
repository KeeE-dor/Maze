"""Maze 基础操作与终端渲染测试。"""
from maze import Maze
from maze.model import E, N, S, W
from maze.render import console


def test_new_maze_is_all_walls():
    m = Maze(3, 3)
    for r in range(3):
        for c in range(3):
            for d in (N, E, S, W):
                assert m.has_wall(r, c, d)


def test_set_wall_clears_only_one_side():
    m = Maze(2, 2)
    m.set_wall(0, 0, E, present=False)
    assert not m.has_wall(0, 0, E)
    assert m.has_wall(0, 1, W)


def test_render_marks_start_end_path():
    m = Maze(2, 2)
    text = console.render(m, path=[(0, 1)])
    assert text.count("S") == 1
    assert text.count("E") == 1
    assert text.count("*") == 1
