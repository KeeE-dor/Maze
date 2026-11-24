"""DFS、BFS、Dijkstra 与 A* 求解器测试。"""
from __future__ import annotations

from pathlib import Path
import random

import pytest

from main import carve_demo_maze, demo_path
from maze.generators import kruskal, prim, recursive_backtracker, recursive_division
from maze.model import Maze
from maze.solvers import astar, bfs, dfs, dijkstra

SOLVERS = {
    "dfs_recursive": dfs.solve_recursive,
    "dfs_iterative": dfs.solve_iterative,
    "bfs_queue": bfs.solve_queue,
    "bfs_recursive": bfs.solve_recursive,
    "dijkstra": dijkstra.solve,
    "astar": astar.solve,
}

GENERATORS = {
    "kruskal": kruskal.generate,
    "prim": prim.generate,
    "backtracker": recursive_backtracker.generate,
    "division": recursive_division.generate,
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
    assert result.cost == len(demo_path(maze)) - 1


@pytest.mark.parametrize("name", SOLVERS)
def test_snake_maze_default_end_stops_at_end(name):
    maze = carve_demo_maze()
    full = demo_path(maze)
    prefix = full[: full.index(maze.end) + 1]
    result = SOLVERS[name](maze)
    assert result.path == prefix
    assert result.path[-1] == maze.end


@pytest.mark.parametrize("name", SOLVERS)
@pytest.mark.parametrize("gen_name", GENERATORS)
@pytest.mark.parametrize("rows,cols", [(2, 2), (5, 5), (8, 12), (15, 15)])
def test_random_mazes_pass_path_checks(name, gen_name, rows, cols):
    maze = GENERATORS[gen_name](rows, cols, rng=random.Random(rows * 100 + cols))
    result = SOLVERS[name](maze)
    assert_valid_path(maze, result)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_all_versions_agree_on_perfect_maze_path(seed):
    maze = kruskal.generate(10, 10, rng=random.Random(seed))
    results = {name: fn(maze) for name, fn in SOLVERS.items()}
    for res in results.values():
        assert res.found
    first_path = results["dfs_recursive"].path
    for res in results.values():
        assert res.path == first_path
    assert results["bfs_queue"].visited_order == results["bfs_recursive"].visited_order
    assert results["bfs_queue"].expanded == results["bfs_recursive"].expanded


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


def test_weighted_mud_maze_astar_and_dijkstra_avoid_mud():
    """带权泥地迷宫中，BFS 只看最少步数直穿泥地，而 Dijkstra 与 A* 会绕行以获得更低总代价。"""
    maze = Maze(4, 4)
    # 少步数但穿过泥地的路径（6 步）
    mud_edges = [
        ((0, 0), (0, 1)), ((0, 1), (0, 2)), ((0, 2), (0, 3)),
        ((0, 3), (1, 3)), ((1, 3), (2, 3)), ((2, 3), (3, 3)),
    ]
    # 多绕两步但全为平地的路径（8 步）
    flat_edges = [
        ((0, 0), (1, 0)), ((1, 0), (1, 1)), ((1, 1), (2, 1)),
        ((2, 1), (2, 0)), ((2, 0), (3, 0)), ((3, 0), (3, 1)),
        ((3, 1), (3, 2)), ((3, 2), (3, 3)),
    ]
    for a, b in mud_edges + flat_edges:
        maze.remove_wall_between(a, b)
    for r, c in ((0, 2), (0, 3), (1, 3)):
        maze.weights[r][c] = 5

    r_bfs = bfs.solve_queue(maze)
    r_dijk = dijkstra.solve(maze)
    r_astar = astar.solve(maze)

    assert len(r_bfs.path) == 7 and r_bfs.cost == 18
    assert len(r_dijk.path) == 9 and r_dijk.cost == 8
    assert len(r_astar.path) == 9 and r_astar.cost == 8
    assert r_astar.cost == r_dijk.cost < r_bfs.cost


def test_astar_expands_far_fewer_nodes_on_open_grid():
    """在空旷网格中，A* 借助曼哈顿启发函数直奔终点，扩展节点数远少于 BFS 与 Dijkstra。"""
    maze = Maze(10, 10)
    maze.clear_internal_walls()
    r_bfs = bfs.solve_queue(maze)
    r_dijk = dijkstra.solve(maze)
    r_astar = astar.solve(maze)

    assert r_astar.cost == r_dijk.cost == r_bfs.cost == 18
    assert r_astar.expanded < r_dijk.expanded
    assert r_astar.expanded < r_bfs.expanded


def test_dijkstra_and_astar_use_handwritten_min_heap():
    root = Path(__file__).resolve().parent.parent / "maze" / "solvers"
    for filename in ("dijkstra.py", "astar.py"):
        src = (root / filename).read_text(encoding="utf-8")
        assert "heapq" not in src
        assert "MinHeap" in src


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


def test_dfs_recursive_records_visit_and_backtrack_trace():
    """在含死胡同的迷宫中，递归版 DFS 的 trace 应准确记录进入与死路回溯事件。"""
    maze = Maze(2, 3)
    # 东向支路 (0,0)->(0,1)->(0,2) 是死胡同（在 neighbors() 中 E 优先于 S）
    maze.remove_wall_between((0, 0), (0, 1))
    maze.remove_wall_between((0, 1), (0, 2))
    # 南向通路 (0,0)->(1,0)->(1,1)->(1,2) 通往终点 (1,2)
    maze.remove_wall_between((0, 0), (1, 0))
    maze.remove_wall_between((1, 0), (1, 1))
    maze.remove_wall_between((1, 1), (1, 2))

    result = dfs.solve_recursive(maze)
    assert result.found
    assert result.path == [(0, 0), (1, 0), (1, 1), (1, 2)]

    visits = [cell for action, cell in result.trace if action == "visit"]
    backtracks = [cell for action, cell in result.trace if action == "backtrack"]
    assert visits == result.visited_order
    # 先探入死胡同 (0,1),(0,2)，再依次回溯退出 (0,2),(0,1)
    assert backtracks == [(0, 2), (0, 1)]
    assert set(backtracks).isdisjoint(set(result.path))
