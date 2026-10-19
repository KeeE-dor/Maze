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
    """生成 rows×cols 的完美迷宫（Kruskal + 随机权 + 手写堆/并查集）。

    TODO 第 3 周：按模块 docstring 里的伪码实现。
    实现后第 5 周的验证脚本应能证明：拆墙数 == rows*cols-1 且全连通。
    """
    raise NotImplementedError("TODO 第 3 周：Kruskal 生成")
