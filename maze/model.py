"""迷宫核心数据模型。

使用 4 位掩码表示单元格四面墙（N=1, E=2, S=4, W=8），初始值为 15（四面全墙）。
拆墙时必须同步清除当前格与相邻格的相反方向位。
"""
from __future__ import annotations

from dataclasses import dataclass, field
import random

N, E, S, W = 1, 2, 4, 8
ALL_WALLS = N | E | S | W
OPPOSITE = {N: S, S: N, E: W, W: E}
DELTA = {N: (-1, 0), E: (0, 1), S: (1, 0), W: (0, -1)}


@dataclass
class SolveResult:
    """求解器统一返回结果。

    path: 起点到终点的完整路径，无解时为空。
    visited_order: 节点首次被访问的顺序，供动画回放使用。
    found: 是否到达终点。
    expanded: 实际扩展（出队或弹栈）的节点数。
    """

    path: list[tuple[int, int]] = field(default_factory=list)
    visited_order: list[tuple[int, int]] = field(default_factory=list)
    found: bool = False
    expanded: int = 0


class Maze:
    def __init__(self, rows: int, cols: int):
        if rows < 2 or cols < 2:
            raise ValueError("迷宫至少需要 2×2")
        self.rows, self.cols = rows, cols
        self.walls = [[ALL_WALLS] * cols for _ in range(rows)]
        self.start = (0, 0)
        self.end = (rows - 1, cols - 1)

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def has_wall(self, r: int, c: int, direction: int) -> bool:
        """检查格子 (r, c) 在指定方向上是否有墙。"""
        return bool(self.walls[r][c] & direction)

    def set_wall(self, r: int, c: int, direction: int, present: bool = True) -> None:
        """设置单侧墙状态（present=True 立墙，False 拆墙）。"""
        if present:
            self.walls[r][c] |= direction
        else:
            self.walls[r][c] &= ~direction

    def neighbors(self, r: int, c: int) -> list[tuple[int, int]]:
        """返回 (r, c) 四周无墙阻隔且在界内的相邻格列表。"""
        ref = []
        for direction in DELTA:
            new_r, new_c = r + DELTA[direction][0], c + DELTA[direction][1]
            if self.in_bounds(new_r, new_c) and not self.has_wall(r, c, direction):
                ref.append((new_r, new_c))
        return ref

    def remove_wall_between(self, a: tuple[int, int], b: tuple[int, int]) -> None:
        """同步拆除相邻两格 a 与 b 之间的墙。"""
        dr, dc = a[0] - b[0], a[1] - b[1]
        if abs(dr) + abs(dc) != 1:
            raise ValueError("Cells are not adjacent")
        if dr == -1 and dc == 0:
            self.set_wall(a[0], a[1], S, False)
            self.set_wall(b[0], b[1], N, False)
        elif dr == 1 and dc == 0:
            self.set_wall(a[0], a[1], N, False)
            self.set_wall(b[0], b[1], S, False)
        elif dr == 0 and dc == -1:
            self.set_wall(a[0], a[1], E, False)
            self.set_wall(b[0], b[1], W, False)
        elif dr == 0 and dc == 1:
            self.set_wall(a[0], a[1], W, False)
            self.set_wall(b[0], b[1], E, False)

    def cell_id(self, r: int, c: int) -> int:
        """二维坐标转一维线性编号。O(1)。"""
        return r * self.cols + c

    def to_point(self, cell_id: int) -> tuple[int, int]:
        """一维线性编号转二维坐标。O(1)。"""
        return cell_id // self.cols, cell_id % self.cols

    @classmethod
    def generate(
        cls,
        rows: int,
        cols: int,
        method: str = "kruskal",
        rng: random.Random | None = None,
    ) -> Maze:
        """按指定生成算法构建迷宫。"""
        if method == "kruskal":
            from maze.generators.kruskal import generate

            return generate(rows, cols, rng=rng)
        elif method == "prim":
            from maze.generators.prim import generate

            return generate(rows, cols, rng=rng)
        else:
            raise ValueError(f"Unknown generator: {method}")
