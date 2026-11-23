"""Kruskal 迷宫生成：为所有内部墙赋随机权，用最小堆与并查集构建最小生成树。"""
from __future__ import annotations

import random

from maze.ds.min_heap import MinHeap
from maze.ds.union_find import UnionFind
from maze.model import Maze


def generate(rows: int, cols: int, rng: random.Random | None = None) -> Maze:
    """使用堆优化 Kruskal 算法生成 rows×cols 完美迷宫。O(E log E) = O(cells log cells)，空间 O(cells)。"""
    if rng is None:
        rng = random.Random()
    maze = Maze(rows, cols)
    total_cells = rows * cols
    uf = UnionFind(total_cells)
    heap = MinHeap()

    for r in range(rows):
        for c in range(cols):
            if c + 1 < cols:
                heap.push((rng.random(), r, c, r, c + 1))
            if r + 1 < rows:
                heap.push((rng.random(), r, c, r + 1, c))

    removed = 0
    target_removed = total_cells - 1
    while removed < target_removed and not heap.is_empty():
        _, ar, ac, br, bc = heap.pop()
        ia = maze.cell_id(ar, ac)
        ib = maze.cell_id(br, bc)
        if not uf.connected(ia, ib):
            maze.remove_wall_between((ar, ac), (br, bc))
            uf.union(ia, ib)
            removed += 1
    return maze
