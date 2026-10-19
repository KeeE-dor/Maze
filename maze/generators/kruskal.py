"""堆优化 Kruskal 迷宫生成（A 同学 · 第 3 周）。

核心思想：把"生成迷宫"看成图的最小生成树问题——
    * 每个格子是一个顶点；相邻两格之间有一条候选边（= 一堵可拆的内部墙）；
    * 给每条边赋【随机】权重，全部放入手写 MinHeap；
    * 循环弹最小边：若两端格子还【不连通】（手写 UnionFind 判断）
      -> 拆墙 + union；已连通则丢弃（拆了会成环）；
    * 恰好拆掉 rows*cols - 1 堵墙后停止。

为什么结果是"完美迷宫"（任意两格恰好一条路径，答辩高频题）：
每次拆墙都合并两个不同的连通分量、从不成环；结束时连通分量从 rows*cols
个减到 1 个，边数 = 顶点数 - 1 —— 这正是生成树的定义。

格子的线性编号（并查集要一维下标）：id(r, c) = r * cols + c。

伪码（对照着写）：
    maze = Maze(rows, cols)
    uf = UnionFind(rows * cols)
    heap = MinHeap()
    for r, c 的每个内部相邻对 (a, b):
        heap.push((rng.random(), *a, *b))
    removed = 0
    while removed < rows * cols - 1:
        _, ar, ac, br, bc = heap.pop()
        ia, ib = id(ar, ac), id(br, bc)
        if not uf.connected(ia, ib):
            maze.remove_wall_between((ar, ac), (br, bc))
            uf.union(ia, ib)
            removed += 1
    return maze
"""
from __future__ import annotations

import random
from maze.ds.min_heap import MinHeap
from maze.ds.union_find import UnionFind
from maze.model import Maze


def generate(rows: int, cols: int, rng: random.Random | None = None) -> Maze:
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
                heap.push((rng.random(), r, c, r+1, c))

    removed = 0
    target_removed = total_cells - 1
    # 当还没拆够 rows*cols - 1 堵墙且堆里还有墙时
    while removed < target_removed and not heap.is_empty():
        # 弹出权重最小的一面墙
        _, ar, ac, br, bc = heap.pop()
        ia = maze.cell_id(ar, ac)
        ib = maze.cell_id(br, bc)
        # 用并查集判断：两端格子是否已经连通？
        if not uf.connected(ia, ib):
            # 还没连通：拆除两者之间的墙！
            maze.remove_wall_between((ar, ac), (br, bc))
            # 在并查集中将它们合并为一个连通块
            uf.union(ia, ib)
            removed += 1
    return maze



