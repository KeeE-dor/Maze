"""
Maze 数据模型 —— 全项目的接口契约，两人共同维护，改动必须一起确认（见 项目计划.md 3.3）。

迷宫表示：rows × cols 网格，walls[r][c] 是一个 4 位整数（位掩码）：

        N = 1   北（上）
        E = 2   东（右）
        S = 4   南（下）
        W = 8   西（左）

初始值 15（二进制 1111，四面全墙）。
"拆掉 (r,c) 与东侧相邻格之间的墙" = walls[r][c] 清掉 E 位，
同时 walls[r][c+1] 清掉 W 位 —— 两侧必须同时改。

为什么用位掩码而不是邻接表？
  * 一个 int 存四面墙，内存约为邻接表 1/8，遍历时缓存友好；
  * "墙"是本项目的业务语义，has_wall / set_wall 读起来最直白；
  * 答辩考点：也要能讲邻接表什么时候更合适（见 项目计划.md 第八节 Q&A 第 5 条）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

N, E, S, W = 1, 2, 4, 8
ALL_WALLS = N | E | S | W
OPPOSITE = {N: S, S: N, E: W, W: E}
DELTA = {N: (-1, 0), E: (0, 1), S: (1, 0), W: (0, -1)}  # 方向 -> (dr, dc)


@dataclass
class SolveResult:
    """所有求解器的统一返回值（渲染与对比实验只认这个结构）。

    path:          起点→终点的完整路径；无解时为空列表
    visited_order: 各节点【首次被访问】的顺序，Pygame 步进动画按它逐帧回放
    found:         是否到达终点
    expanded:      实际扩展（出队/弹栈）的节点数，BFS/DFS 对比实验用
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
        self.walls = [[ALL_WALLS] * cols for _ in range(rows)]  # 初始全墙
        self.start = (0, 0)
        self.end = (rows - 1, cols - 1)


    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def has_wall(self, r: int, c: int, direction: int) -> bool:
        """格子 (r,c) 在 direction 方向上是否有墙。"""
        return bool(self.walls[r][c] & direction)

    def set_wall(self, r: int, c: int, direction: int, present: bool = True) -> None:
        """present=True 立墙 / False 拆墙。"""
        if present:
            self.walls[r][c] |= direction
        else:
            self.walls[r][c] &= ~direction

    def neighbors(self, r: int, c: int) -> list[tuple[int, int]]:
        """返回 (r,c) 四周【没有被墙隔开】且在界内的相邻格坐标列表。"""
        ref = []
        for direction in DELTA:
            new_r , new_c  =r + DELTA[direction][0], c + DELTA[direction][1]
            if self.in_bounds(new_r , new_c) and not self.has_wall(r, c, direction):
                ref.append((new_r, new_c))
        return ref

    def remove_wall_between(self, a: tuple[int, int], b: tuple[int, int]) -> None:
        """拆掉相邻两格 a、b 之间的墙"""

        dr, dc = a[0] - b[0], a[1] - b[1]
        if abs(dr) + abs(dc) != 1:
            raise ValueError("Cells are not adjacent")
        #a在b上面
        if dr == -1 and dc == 0 :
            self.set_wall(a[0], a[1], S,False)
            self.set_wall(b[0],b[1],N,False)
        #a在b下面
        elif dr == 1 and dc == 0 :
            self.set_wall(a[0], a[1], N, False)
            self.set_wall(b[0],b[1],S,False)
        #a在b左边
        elif dr == 0 and dc == -1 :
            self.set_wall(a[0], a[1], E, False)
            self.set_wall(b[0],b[1],W,False)
        #a在b右边
        elif dr == 0 and dc == 1 :
            self.set_wall(a[0], a[1], W, False)
            self.set_wall(b[0],b[1],E,False)
        return

    def cell_id(self, r: int, c: int) -> int:
        #二维转一维
        return r * self.cols + c

    def to_point(self, id: int) -> tuple[int, int]:
        #一维转二维
        return id // self.cols, id % self.cols

    #生成迷宫
    @classmethod
    def generate(self,rows: int, cols: int,method = "kruskal") -> Maze:
        if method == "kruskal":
            from maze.generators.kruskal import generate
            return generate(rows,cols)
        elif method == "prim":
            from maze.generators.prim import generate
            return generate(rows,cols)
        else:
            raise ValueError(f"Unknown generator: {method}")

