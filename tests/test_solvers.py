"""求解器验收门（B 同学 · 第 3 周）—— 之后所有求解器（BFS 两版等）都要过这三查。

路径三查（通用合法性）：
    1. 首尾格正确：path[0]==start 且 path[-1]==end；
    2. 相邻两步不穿墙：后一格必须在前一格的 neighbors() 里；
    3. 路径无重复格（简单路径）。

确定性用例用 main.py 的硬编码蛇形迷宫：它是单条走廊，路径唯一，
两版 DFS 的 path、visited_order、expanded 都可以精确断言。
"""
from __future__ import annotations

import random

import pytest

from main import carve_demo_maze, demo_path
from maze.generators import kruskal, prim
from maze.solvers import dfs

SOLVERS = {"dfs_recursive": dfs.solve_recursive, "dfs_iterative": dfs.solve_iterative}


def assert_valid_path(maze, result, start=None, end=None) -> None:
    """三查：首尾正确 / 相邻不穿墙 / 无重复格。found 必须为 True。"""
    start = maze.start if start is None else start
    end = maze.end if end is None else end
    assert result.found
    assert result.path[0] == start          # 查 1：首格
    assert result.path[-1] == end           # 查 1：尾格
    for a, b in zip(result.path, result.path[1:]):
        assert b in maze.neighbors(*a)      # 查 2：相邻且无墙
    assert len(set(result.path)) == len(result.path)  # 查 3：无重复


# ---------- 确定性：蛇形迷宫（路径唯一，可精确断言） ----------

@pytest.mark.parametrize("name", SOLVERS)
def test_snake_maze_exact_path(name):
    """单走廊迷宫：显式把终点设为走廊尽头 (5,0)，
    路径/访问序/扩展数必须精确等于整条走廊。"""
    maze = carve_demo_maze()
    result = SOLVERS[name](maze, end=(5, 0))
    assert result.path == demo_path(maze)
    assert result.visited_order == demo_path(maze)   # 无分支：访问序就是走廊
    assert result.expanded == len(demo_path(maze))


@pytest.mark.parametrize("name", SOLVERS)
def test_snake_maze_default_end_stops_at_end(name):
    """默认终点是 (5,5)（构造器取右下角），走廊还在它之后延伸 5 格——
    找到终点必须立刻收手：path 恰为走廊前缀，一格不多。"""
    maze = carve_demo_maze()
    full = demo_path(maze)
    prefix = full[: full.index(maze.end) + 1]
    result = SOLVERS[name](maze)
    assert result.path == prefix
    assert result.path[-1] == maze.end


# ---------- 通用：随机完美迷宫上的三查 ----------

@pytest.mark.parametrize("name", SOLVERS)
@pytest.mark.parametrize("gen_name", ["kruskal", "prim"])
@pytest.mark.parametrize("rows,cols", [(2, 2), (5, 5), (8, 12), (15, 15)])
def test_random_mazes_pass_path_checks(name, gen_name, rows, cols):
    gen = kruskal.generate if gen_name == "kruskal" else prim.generate
    maze = gen(rows, cols, rng=random.Random(rows * 100 + cols))
    result = SOLVERS[name](maze)
    assert_valid_path(maze, result)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_both_versions_agree_on_path(seed):
    """完美迷宫是树：两点间简单路径唯一，两版 DFS 的 path 必须完全一致。"""
    maze = kruskal.generate(10, 10, rng=random.Random(seed))
    r1 = dfs.solve_recursive(maze)
    r2 = dfs.solve_iterative(maze)
    assert r1.path == r2.path
    assert r1.found and r2.found


# ---------- 边界 ----------

@pytest.mark.parametrize("name", SOLVERS)
def test_start_equals_end(name):
    maze = carve_demo_maze()
    result = SOLVERS[name](maze, start=(3, 0), end=(3, 0))
    assert result.found
    assert result.path == [(3, 0)]
    assert result.visited_order == [(3, 0)]
    assert result.expanded == 1


@pytest.mark.parametrize("name", SOLVERS)
def test_unreachable_returns_not_found(name):
    """全墙迷宫：除起点外哪都去不了，found=False 且 path 为空。"""
    maze = carve_demo_maze()
    for r in range(maze.rows):          # 重新封死所有墙（制造不可达）
        for c in range(maze.cols):
            maze.walls[r][c] = 15
    result = SOLVERS[name](maze, end=(maze.rows - 1, maze.cols - 1))
    assert not result.found
    assert result.path == []
    assert result.expanded == 1         # 只扩展了起点
