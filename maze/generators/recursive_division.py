"""递归分割迷宫生成算法（Recursive Division）。

核心思想：
与“从全墙开始拆墙”的算法相反，递归分割从内部完全打通的大房间起步：
1. 在房间内部随机挑一行（横切）或一列（竖切）筑起一堵分隔墙，将房间一分为二；
2. 在这堵新墙上随机留出一个“门洞”保持两侧连通；
3. 对分割出的两个子房间递归执行相同操作，直到子房间宽高小于 2。
特点：迷宫由清晰的矩形大厅和隔断构成，视觉风格鲜明。
"""
from __future__ import annotations

import random

from maze.model import Maze


def generate(rows: int, cols: int, rng: random.Random | None = None) -> Maze:
    """使用递归分割法生成 rows×cols 完美迷宫。时间 O(cells log cells)，空间 O(log(rows+cols))。"""
    if rng is None:
        rng = random.Random()

    maze = Maze(rows, cols)
    # 初始清空所有内部墙体、只保留外框（并标记 initial_open=True 供动画筑墙回放）
    maze.clear_internal_walls()

    def _divide(r0: int, c0: int, h: int, w: int) -> None:
        if h < 2 or w < 2:
            return

        # 宽大于高时竖切，高大于宽时横切，正方形时随机决定，使房间尽量规整
        if w > h:
            horizontal = False
        elif h > w:
            horizontal = True
        else:
            horizontal = rng.choice((True, False))

        if horizontal:
            # 在 split_r 与 split_r + 1 行之间筑一道横墙，并随机留一列作门洞
            split_r = rng.randint(r0, r0 + h - 2)
            hole_c = rng.randint(c0, c0 + w - 1)
            for c in range(c0, c0 + w):
                if c != hole_c:
                    maze.add_wall_between((split_r, c), (split_r + 1, c))
            _divide(r0, c0, split_r - r0 + 1, w)
            _divide(split_r + 1, c0, r0 + h - 1 - split_r, w)
        else:
            # 在 split_c 与 split_c + 1 列之间筑一道竖墙，并随机留一行作门洞
            split_c = rng.randint(c0, c0 + w - 2)
            hole_r = rng.randint(r0, r0 + h - 1)
            for r in range(r0, r0 + h):
                if r != hole_r:
                    maze.add_wall_between((r, split_c), (r, split_c + 1))
            _divide(r0, c0, h, split_c - c0 + 1)
            _divide(r0, split_c + 1, h, c0 + w - 1 - split_c)

    _divide(0, 0, rows, cols)
    return maze
