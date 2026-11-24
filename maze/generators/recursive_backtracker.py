"""递归回溯迷宫生成算法（DFS 生成）。

核心思想：
从起点出发随机选择尚未访问的邻居打通墙壁并继续前进；
当走到死胡同时退回栈顶上一个还有未访问邻居的格子继续探索，直到所有格子都走遍。
特点：生成长主干、曲折蜿蜒、死胡同相对较少的迷宫。
"""
from __future__ import annotations

import random

from maze.ds.stack import Stack
from maze.model import DELTA, Maze


def generate(rows: int, cols: int, rng: random.Random | None = None) -> Maze:
    """使用手写栈实现迭代版递归回溯生成 rows×cols 完美迷宫。O(cells)，空间 O(cells)。"""
    if rng is None:
        rng = random.Random()

    maze = Maze(rows, cols)
    visited: set[tuple[int, int]] = {(0, 0)}
    stack = Stack()
    stack.push((0, 0))

    while not stack.is_empty():
        r, c = stack.peek()
        # 收集当前格子四周界内且尚未加入迷宫的邻居
        candidates: list[tuple[int, int]] = []
        for dr, dc in DELTA.values():
            nr, nc = r + dr, c + dc
            if maze.in_bounds(nr, nc) and (nr, nc) not in visited:
                candidates.append((nr, nc))

        if candidates:
            # 随机挑一个未访问邻居打通墙壁并继续深入
            nxt = rng.choice(candidates)
            maze.remove_wall_between((r, c), nxt)
            visited.add(nxt)
            stack.push(nxt)
        else:
            # 四周都已访问过，退回上一格继续寻找分叉
            stack.pop()

    return maze
