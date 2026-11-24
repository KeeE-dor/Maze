"""Prim 迷宫生成算法。

核心思想（像植物从种子发芽一样局部向外生长）：
1. 从起点 (0, 0) 出发，把它标记为“已访问”，并把它四周的内部墙（frontier 边界墙）赋予随机权重放进最小堆；
2. 每次从堆顶弹出权重最小的墙：
   - 如果墙对面的格子还没被访问：拆掉这堵墙，把新格子标记为已访问，再把新格子通往其它未访问邻居的墙放进堆里；
   - 如果墙对面的格子已经被访问过了：直接丢弃（拆了会成环）；
3. 重复直到所有格子都被访问过为止。相比 Kruskal，Prim 只需要一个 visited 集合，不需要并查集。
"""
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

    # 从 (0, 0) 作为种子开始生长
    start_cell = (0, 0)
    visited.add(start_cell)

    def add_wall(r: int, c: int) -> None:
        """把 (r, c) 通往所有未访问邻居的墙，加上随机权重放进最小堆。"""
        for dr, dc in DELTA.values():
            nr, nc = r + dr, c + dc
            if maze.in_bounds(nr, nc) and (nr, nc) not in visited:
                heap.push((rng.random(), r, c, nr, nc))

    add_wall(*start_cell)

    total = rows * cols
    # 只要还有格子没被纳入迷宫，就继续从堆里挑权重最小的边界墙打通
    while len(visited) < total and not heap.is_empty():
        _, r, c, nr, nc = heap.pop()
        # 同一格可能先后被多个邻居推入堆中，弹出时必须再次检查是否已访问
        if (nr, nc) not in visited:
            maze.remove_wall_between((r, c), (nr, nc))
            visited.add((nr, nc))
            add_wall(nr, nc)

    return maze
