"""Prim 迷宫生成（A 同学 · 第 4 周）。

核心思想：像藤蔓生长——从一颗"种子"格子出发，把【frontier 边】
（已访问格与未访问格之间的墙，赋随机权重）放入手写 MinHeap，循环弹最小边：
    * 对面格尚未访问 -> 拆墙、标记访问、把新格通往其它未访问邻居的墙入堆；
    * 对面已访问     -> 丢弃（拆了会成环）；
    直到所有格子都被访问。只需要一个 visited 集合，不需要并查集。

与 Kruskal 的对比（直接写进报告第三章）：
    * Kruskal 全局选边、依赖并查集；Prim 局部生长、只需 visited + 堆；
    * 两者都用手写最小堆，堆的用法不同（Kruskal 一次建堆、Prim 边生长边 push）；
    * 生成的迷宫"手感"不同（Prim 倾向短死胡同多、走廊细；Kruskal 更均匀）——
      第 5 周实验里可以用死胡同数量/路径长度分布做个小对比，很出彩。
"""
from __future__ import annotations

import random

from maze.ds.min_heap import MinHeap
from maze.model import Maze


def generate(rows: int, cols: int, rng: random.Random | None = None) -> Maze:
    """生成 rows×cols 的完美迷宫（Prim + 随机权 frontier 边）。

    TODO 第 4 周：从 (0, 0) 当种子开始生长。
    """
    raise NotImplementedError("TODO 第 4 周：Prim 生成")
