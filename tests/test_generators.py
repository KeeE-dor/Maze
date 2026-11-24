"""迷宫生成器与 Maze 模型测试。"""
from __future__ import annotations

import random

import pytest

from maze.generators import kruskal, prim, recursive_backtracker, recursive_division
from maze.model import Maze
from scripts.verify import verify_perfect_maze

GEN_CASES = [
    ("kruskal", kruskal.generate),
    ("prim", prim.generate),
    ("backtracker", recursive_backtracker.generate),
    ("division", recursive_division.generate),
]


@pytest.mark.parametrize("method,gen_fn", GEN_CASES)
@pytest.mark.parametrize("rows,cols", [(2, 2), (5, 7), (12, 12), (20, 15)])
def test_generators_produce_perfect_mazes(method, gen_fn, rows, cols):
    maze = gen_fn(rows, cols, rng=random.Random(rows * 31 + cols))
    ok, msg = verify_perfect_maze(maze)
    assert ok, msg
    if method == "division":
        assert maze.initial_open
        assert len(maze.gen_steps) == (rows - 1) * (cols - 1)
    else:
        assert not maze.initial_open
        assert len(maze.carve_history) == rows * cols - 1
        assert len(maze.gen_steps) == rows * cols - 1


@pytest.mark.parametrize("method,gen_fn", GEN_CASES)
def test_maze_generate_forwards_rng_for_reproducibility(method, gen_fn):
    m1 = Maze.generate(10, 10, method=method, rng=random.Random(99))
    m2 = gen_fn(10, 10, rng=random.Random(99))
    m3 = Maze.generate(10, 10, method=method, rng=random.Random(100))
    assert m1.walls == m2.walls
    assert m1.walls != m3.walls


def test_add_loops_and_weighted_terrain():
    maze = Maze.generate(10, 10, method="kruskal", rng=random.Random(7), loop_ratio=0.15, mud_ratio=0.25)
    assert not verify_perfect_maze(maze)[0]
    assert maze.has_weighted_terrain()
    assert maze.weights[maze.start[0]][maze.start[1]] == 1
    assert maze.weights[maze.end[0]][maze.end[1]] == 1


def test_maze_generate_unknown_method_raises():
    with pytest.raises(ValueError):
        Maze.generate(5, 5, method="unknown")


def test_maze_invalid_size_raises():
    with pytest.raises(ValueError):
        Maze(1, 5)
    with pytest.raises(ValueError):
        Maze(5, 1)


def test_cell_id_and_to_point_roundtrip():
    m = Maze(4, 7)
    for r in range(m.rows):
        for c in range(m.cols):
            cid = m.cell_id(r, c)
            assert m.to_point(cid) == (r, c)
