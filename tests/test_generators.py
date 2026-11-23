"""迷宫生成器与 Maze 模型测试。"""
from __future__ import annotations

import random

import pytest

from maze.generators import kruskal, prim
from maze.model import Maze
from scripts.verify import verify_perfect_maze


@pytest.mark.parametrize("gen_fn", [kruskal.generate, prim.generate])
@pytest.mark.parametrize("rows,cols", [(2, 2), (5, 7), (12, 12), (20, 15)])
def test_generators_produce_perfect_mazes(gen_fn, rows, cols):
    maze = gen_fn(rows, cols, rng=random.Random(rows * 31 + cols))
    ok, msg = verify_perfect_maze(maze)
    assert ok, msg


@pytest.mark.parametrize("method,gen_fn", [("kruskal", kruskal.generate), ("prim", prim.generate)])
def test_maze_generate_forwards_rng_for_reproducibility(method, gen_fn):
    m1 = Maze.generate(10, 10, method=method, rng=random.Random(99))
    m2 = gen_fn(10, 10, rng=random.Random(99))
    m3 = Maze.generate(10, 10, method=method, rng=random.Random(100))
    assert m1.walls == m2.walls
    assert m1.walls != m3.walls


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
