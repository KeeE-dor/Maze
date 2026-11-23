"""DFS 与 BFS 求解器测试。"""
from __future__ import annotations

import random

import pytest

from main import carve_demo_maze, demo_path
from maze.generators import kruskal, prim
from maze.model import Maze
from maze.solvers import bfs, dfs

SOLVERS = {
    "dfs_recursive": dfs.solve_recursive,
    "dfs_iterative": dfs.solve_iterative,
    "bfs_queue": bfs.solve_queue,
    "bfs_recursive": bfs.solve_recursive,
}


def assert_valid_path(maze, result, start=None, end=None) -> None:
    """检查路径首尾正确、相邻步无墙且不含重复格。"""
    start = maze.start if start is None else start
    end = maze.end if end is None else end
    assert result.found
    assert result.path[0] == start
    assert result.path[-1] == end
    for a, b in zip(result.path, result.path[1:]):
        assert b in maze.neighbors(*a)
    assert len(set(result.path)) == len(result.path)


@pytest.mark.parametrize("name", SOLVERS)
def test_snake_maze_exact_path(name):
    maze = carve_demo_maze()
    result = SOLVERS[name](maze, end=(5, 0))
    assert result.path == demo_path(maze)
    assert result.visited_order == demo_path(maze)
    assert result.expanded == len(demo_path(maze))


@pytest.mark.parametrize("name", SOLVERS)
def test_snake_maze_default_end_stops_at_end(name):
    maze = carve_demo_maze()
    full = demo_path(maze)
    prefix = full[: full.index(maze.end) + 1]
    result = SOLVERS[name](maze)
    assert result.path == prefix
    assert result.path[-1] == maze.end


@pytest.mark.parametrize("name", SOLVERS)
@pytest.mark.parametrize("gen_name", ["kruskal", "prim"])
@pytest.mark.parametrize("rows,cols", [(2, 2), (5, 5), (8, 12), (15, 15)])
def test_random_mazes_pass_path_checks(name, gen_name, rows, cols):
    gen = kruskal.generate if gen_name == "kruskal" else prim.generate
    maze = gen(rows, cols, rng=random.Random(rows * 100 + cols))
    result = SOLVERS[name](maze)
    assert_valid_path(maze, result)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_all_versions_agree_on_perfect_maze_path(seed):
    maze = kruskal.generate(10, 10, rng=random.Random(seed))
    r_dfs_r = dfs.solve_recursive(maze)
    r_dfs_i = dfs.solve_iterative(maze)
    r_bfs_q = bfs.solve_queue(maze)
    r_bfs_r = bfs.solve_recursive(maze)

    assert r_dfs_r.found and r_dfs_i.found and r_bfs_q.found and r_bfs_r.found
    assert r_dfs_r.path == r_dfs_i.path == r_bfs_q.path == r_bfs_r.path
    assert r_bfs_q.visited_order == r_bfs_r.visited_order
    assert r_bfs_q.expanded == r_bfs_r.expanded


def test_bfs_finds_shortest_path_on_cyclic_maze():
    """含环迷宫中，BFS 必须找到 7 格最短路并短于 DFS 的 11 格绕路。"""
    maze = Maze(4, 4)
    short_edges = [
        ((0, 0), (1, 0)), ((1, 0), (2, 0)), ((2, 0), (3, 0)),
        ((3, 0), (3, 1)), ((3, 1), (3, 2)), ((3, 2), (3, 3)),
    ]
    long_edges = [
        ((0, 0), (0, 1)), ((0, 1), (0, 2)), ((0, 2), (0, 3)),
        ((0, 3), (1, 3)), ((1, 3), (1, 2)), ((1, 2), (1, 1)),
        ((1, 1), (2, 1)), ((2, 1), (2, 2)), ((2, 2), (2, 3)), ((2, 3), (3, 3)),
    ]
    for a, b in short_edges + long_edges:
        maze.remove_wall_between(a, b)

    r_bfs_q = bfs.solve_queue(maze)
    r_bfs_r = bfs.solve_recursive(maze)
    r_dfs_r = dfs.solve_recursive(maze)
    r_dfs_i = dfs.solve_iterative(maze)

    for res in (r_bfs_q, r_bfs_r, r_dfs_r, r_dfs_i):
        assert_valid_path(maze, res)

    assert len(r_bfs_q.path) == 7
    assert len(r_bfs_r.path) == 7
    assert len(r_dfs_r.path) == 11
    assert len(r_bfs_q.path) < len(r_dfs_r.path)


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
    maze = carve_demo_maze()
    for r in range(maze.rows):
        for c in range(maze.cols):
            maze.walls[r][c] = 15
    result = SOLVERS[name](maze, end=(maze.rows - 1, maze.cols - 1))
    assert not result.found
    assert result.path == []
    assert result.expanded == 1
