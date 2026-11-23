"""验证脚本的反例检测测试。"""
from __future__ import annotations

import random

from maze.generators import kruskal
from maze.model import E, Maze, SolveResult
from maze.solvers import bfs
from scripts.verify import (
    verify_cross_algorithms,
    verify_perfect_maze,
    verify_solution_path,
)


def test_verify_perfect_maze_detects_cycle():
    maze = kruskal.generate(5, 5, rng=random.Random(7))
    for r in range(maze.rows):
        for c in range(maze.cols - 1):
            if maze.has_wall(r, c, E):
                maze.remove_wall_between((r, c), (r, c + 1))
                ok, _ = verify_perfect_maze(maze)
                assert not ok
                return
    raise AssertionError("未找到可拆内部墙")


def test_verify_perfect_maze_detects_disconnected():
    maze = Maze(4, 4)
    ok, _ = verify_perfect_maze(maze)
    assert not ok


def test_verify_perfect_maze_detects_asymmetric_wall():
    maze = kruskal.generate(4, 4, rng=random.Random(3))
    maze.set_wall(0, 0, E, present=False)
    maze.set_wall(0, 1, 8, present=True)
    ok, msg = verify_perfect_maze(maze)
    assert not ok
    assert "不对称" in msg


def test_verify_solution_path_rejects_wall_crossing():
    maze = Maze(3, 3)
    bad = SolveResult(path=[(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)], found=True, expanded=5)
    ok, msg = verify_solution_path(maze, bad)
    assert not ok
    assert "穿墙" in msg


def test_verify_solution_path_rejects_wrong_endpoints_and_duplicates():
    maze = kruskal.generate(4, 4, rng=random.Random(11))
    good = bfs.solve_queue(maze)

    wrong_start = SolveResult(path=good.path[1:], found=True, expanded=good.expanded)
    assert not verify_solution_path(maze, wrong_start)[0]

    dup_path = SolveResult(
        path=good.path + [good.path[-1]],
        found=True,
        expanded=good.expanded,
    )
    assert not verify_solution_path(maze, dup_path)[0]


def test_verify_cross_algorithms_passes_on_generated_maze():
    maze = kruskal.generate(8, 8, rng=random.Random(12))
    ok, _ = verify_cross_algorithms(maze, is_perfect=True)
    assert ok
