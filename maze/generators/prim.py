"""Prim 迷宫生成：从起点向外扩展 frontier 边，通过最小堆按随机权生长。"""
from __future__ import annotations

import random

from maze.ds.min_heap import MinHeap
from maze.model import DELTA, Maze


def generate(rows: int, cols: int, rng: random.Random | None = None) -> Maze:
    """使用 Prim 算法生成 rows×cols 完美迷宫。O(E log E) = O(cells log cells)，空间 O(cells)。"""
    if rng is None:
        rng = random.Random()
    maze = Maze(rows, cols)
    heap = MinHeap()
    visited: set[tuple[int, int]] = set()
    start_cell = (0, 0)
    visited.add(start_cell)

    def add_wall(r: int, c: int) -> None:
        for dr, dc in DELTA.values():
            nr, nc = r + dr, c + dc
            if maze.in_bounds(nr, nc) and (nr, nc) not in visited:
                heap.push((rng.random(), r, c, nr, nc))

    add_wall(*start_cell)

    total = rows * cols
    while len(visited) < total and not heap.is_empty():
        _, r, c, nr, nc = heap.pop()
        if (nr, nc) not in visited:
            maze.remove_wall_between((r, c), (nr, nc))
            visited.add((nr, nc))
            add_wall(nr, nc)

    return maze
