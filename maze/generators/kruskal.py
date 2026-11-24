"""堆优化 Kruskal 迷宫生成算法。

核心思想（把迷宫生成看作求图的随机最小生成树）：
1. 每个格子是一个顶点，相邻两格之间的内部墙是一条候选边；
2. 给所有内部墙分配 0~1 的随机权重，全部放进手写 MinHeap（最小堆）；
3. 每次从堆顶弹出权重最小的墙，用 UnionFind（并查集）检查墙两侧的格子是否已经连通：
   - 若尚未连通：拆掉这堵墙，并在并查集中合并两个格子；
   - 若已经连通：说明有别的路可走，再拆就会产生环，直接跳过；
4. 只要拆掉 rows*cols - 1 堵墙，所有格子就恰好连成一棵生成树（完美迷宫，任意两点只有唯一路径）。
"""
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

    # 遍历每个格子，只收集它的右墙（东）和下墙（南），避免同一堵内部墙被重复放进堆里两次
    for r in range(rows):
        for c in range(cols):
            if c + 1 < cols:
                # 元组第一项是随机权重，MinHeap 会按第一项大小排序
                heap.push((rng.random(), r, c, r, c + 1))
            if r + 1 < rows:
                heap.push((rng.random(), r, c, r + 1, c))

    removed = 0
    # 树有 N 个顶点时，边数恰好为 N - 1；拆够这么多堵墙就一定全部连通，可以提前结束
    target_removed = total_cells - 1
    while removed < target_removed and not heap.is_empty():
        _, ar, ac, br, bc = heap.pop()
        ia = maze.cell_id(ar, ac)
        ib = maze.cell_id(br, bc)
        # 如果墙两边还没有路相连，就拆掉并合并集合；如果已经连通，跳过防止成环
        if not uf.connected(ia, ib):
            maze.remove_wall_between((ar, ac), (br, bc))
            uf.union(ia, ib)
            removed += 1
    return maze
