"""能立刻通过的示例测试：验证迷宫模型与终端渲染（已实现部分）。

跑法：项目根目录执行  python -m pytest
第 1 周先读懂这个文件学"怎么写测试"：正常流程 -> 边界 -> 性质（不变式）。
"""
from maze import Maze
from maze.model import N, E, S, W
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
    assert m.has_wall(0, 1, W)  # 对面那侧还在 —— 所以才需要 remove_wall_between()


def test_render_marks_start_end_path():
    m = Maze(2, 2)
    text = console.render(m, path=[(0, 1)])
    assert text.count("S") == 1  # 起点 (0,0)
    assert text.count("E") == 1  # 终点 (1,1)
    assert text.count("*") == 1  # 路径 (0,1)
