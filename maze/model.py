"""迷宫核心数据模型（全项目的公共接口契约）。

位掩码设计说明：
- 每个格子 walls[r][c] 是一个 4 位二进制整数，分别代表四个方向的墙是否存在：
  N=1 (0001 上), E=2 (0010 右), S=4 (0100 下), W=8 (1000 左)
- 初始值 ALL_WALLS = 15 (1111)，表示四面全有墙。
- 拆墙或筑墙时（例如处理 (r,c) 和右边 (r,c+1)），必须同时修改 (r,c) 的 E 位和 (r,c+1) 的 W 位。
"""
from __future__ import annotations

from dataclasses import dataclass, field
import random

# 四个方向的二进制位掩码
N, E, S, W = 1, 2, 4, 8
ALL_WALLS = N | E | S | W  # 15，代表四面都有墙
OPPOSITE = {N: S, S: N, E: W, W: E}  # 方向对应的反方向
DELTA = {N: (-1, 0), E: (0, 1), S: (1, 0), W: (0, -1)}  # 方向对应的行列偏移 (dr, dc)


@dataclass
class SolveResult:
    """所有迷宫求解器统一返回的结果结构。

    path:          起点到终点的完整路径坐标列表；无解时为空列表 []
    visited_order: 算法搜索过程中，节点【首次被访问】的顺序，动画回放按它逐帧播放
    found:         是否成功找到终点
    expanded:      实际扩展（出队或弹栈）的节点数量，用于对比算法搜索效率
    trace:         可选的详细搜索事件流 (action, cell)：
                   "visit" 表示进入探索，"backtrack" 表示死路回溯退出；
                   为空时渲染层按 visited_order 顺序回放
    cost:          路径总代价（无权迷宫中等于步数 len(path)-1，带权地形中为进入各格的权重之和）
    """

    path: list[tuple[int, int]] = field(default_factory=list)
    visited_order: list[tuple[int, int]] = field(default_factory=list)
    found: bool = False
    expanded: int = 0
    trace: list[tuple[str, tuple[int, int]]] = field(default_factory=list)
    cost: int = 0


class Maze:
    def __init__(self, rows: int, cols: int):
        if rows < 2 or cols < 2:
            raise ValueError("迷宫至少需要 2×2")
        self.rows, self.cols = rows, cols
        # 生成 rows 行 cols 列的二维列表，每个格子初始四面全墙（15）
        self.walls = [[ALL_WALLS] * cols for _ in range(rows)]
        # 每个格子的通行代价（默认普通地面为 1，泥地地形设为 5 等高代价）
        self.weights: list[list[int]] = [[1] * cols for _ in range(rows)]
        self.start = (0, 0)                  # 默认起点：左上角
        self.end = (rows - 1, cols - 1)      # 默认终点：右下角
        # 按拆墙先后顺序记录所有被打通的相邻格对 (a, b)，兼容早期拆墙动画接口
        self.carve_history: list[tuple[tuple[int, int], tuple[int, int]]] = []
        # 动画起始模式：False=从全墙开始拆墙；True=从空房间开始筑墙（递归分割法）
        self.initial_open: bool = False
        # 统一生成事件流：("remove", a, b) 表示拆墙，("add", a, b) 表示筑墙
        self.gen_steps: list[tuple[str, tuple[int, int], tuple[int, int]]] = []

    def in_bounds(self, r: int, c: int) -> bool:
        """判断坐标 (r, c) 是否在迷宫合法范围内。"""
        return 0 <= r < self.rows and 0 <= c < self.cols

    def has_wall(self, r: int, c: int, direction: int) -> bool:
        """用按位与检查格子 (r, c) 在 direction 方向上是否有墙。"""
        return bool(self.walls[r][c] & direction)

    def set_wall(self, r: int, c: int, direction: int, present: bool = True) -> None:
        """修改单侧墙状态：present=True 用按位或立墙；present=False 用按位与非拆墙。"""
        if present:
            self.walls[r][c] |= direction
        else:
            self.walls[r][c] &= ~direction

    def neighbors(self, r: int, c: int) -> list[tuple[int, int]]:
        """返回 (r, c) 四周【没有墙阻隔】且在界内的可通行相邻格子列表。"""
        ref = []
        for direction in DELTA:
            new_r, new_c = r + DELTA[direction][0], c + DELTA[direction][1]
            # 只有不出界且该方向没墙，才能走过去
            if self.in_bounds(new_r, new_c) and not self.has_wall(r, c, direction):
                ref.append((new_r, new_c))
        return ref

    def _set_wall_between(self, a: tuple[int, int], b: tuple[int, int], present: bool) -> None:
        """同步立起或拆除相邻两格 a 与 b 之间的墙，保证两侧位掩码始终对称。"""
        dr, dc = a[0] - b[0], a[1] - b[1]
        if abs(dr) + abs(dc) != 1:
            raise ValueError("Cells are not adjacent")
        if dr == -1 and dc == 0:      # a 在 b 上方
            self.set_wall(a[0], a[1], S, present)
            self.set_wall(b[0], b[1], N, present)
        elif dr == 1 and dc == 0:     # a 在 b 下方
            self.set_wall(a[0], a[1], N, present)
            self.set_wall(b[0], b[1], S, present)
        elif dr == 0 and dc == -1:    # a 在 b 左方
            self.set_wall(a[0], a[1], E, present)
            self.set_wall(b[0], b[1], W, present)
        elif dr == 0 and dc == 1:     # a 在 b 右方
            self.set_wall(a[0], a[1], W, present)
            self.set_wall(b[0], b[1], E, present)

    def remove_wall_between(self, a: tuple[int, int], b: tuple[int, int]) -> None:
        """同步拆除相邻两格 a 与 b 之间的墙并记录到生成事件流。"""
        self._set_wall_between(a, b, False)
        self.carve_history.append((a, b))
        self.gen_steps.append(("remove", a, b))

    def add_wall_between(self, a: tuple[int, int], b: tuple[int, int]) -> None:
        """同步立起相邻两格 a 与 b 之间的墙并记录到生成事件流（递归分割法用）。"""
        self._set_wall_between(a, b, True)
        self.gen_steps.append(("add", a, b))

    def clear_internal_walls(self) -> None:
        """清空所有内部墙体、仅保留四周外边界墙，用于递归分割法的空房间初始状态。"""
        for r in range(self.rows):
            for c in range(self.cols):
                mask = 0
                if r == 0:
                    mask |= N
                if r == self.rows - 1:
                    mask |= S
                if c == 0:
                    mask |= W
                if c == self.cols - 1:
                    mask |= E
                self.walls[r][c] = mask
        self.initial_open = True

    def cell_cost(self, r: int, c: int) -> int:
        """返回进入格子 (r, c) 的通行代价（普通格为 1，泥地等高代价地形 > 1）。"""
        return self.weights[r][c]

    def path_cost(self, path: list[tuple[int, int]]) -> int:
        """计算整条路径从起点出发依次步入后续各格子的总通行代价。"""
        if len(path) <= 1:
            return 0
        return sum(self.cell_cost(r, c) for r, c in path[1:])

    def has_weighted_terrain(self) -> bool:
        """判断当前迷宫是否包含高代价泥地等非均匀地形。"""
        return any(w != 1 for row in self.weights for w in row)

    def add_loops(self, ratio: float, rng: random.Random | None = None) -> int:
        """按比例 ratio (0.0~1.0) 随机额外拆除封闭内部墙，将完美迷宫变为含环迷宫。"""
        if ratio <= 0:
            return 0
        if rng is None:
            rng = random.Random()
        candidates: list[tuple[tuple[int, int], tuple[int, int]]] = []
        for r in range(self.rows):
            for c in range(self.cols):
                if c + 1 < self.cols and self.has_wall(r, c, E):
                    candidates.append(((r, c), (r, c + 1)))
                if r + 1 < self.rows and self.has_wall(r, c, S):
                    candidates.append(((r, c), (r + 1, c)))
        if not candidates:
            return 0
        count = max(1, round(len(candidates) * min(1.0, ratio)))
        rng.shuffle(candidates)
        for a, b in candidates[:count]:
            self.remove_wall_between(a, b)
        return min(count, len(candidates))

    def apply_weighted_terrain(
        self,
        ratio: float,
        mud_cost: int = 5,
        rng: random.Random | None = None,
    ) -> int:
        """按比例在非起终点的格子里随机铺设高代价泥地（默认代价 5）。"""
        if ratio <= 0:
            return 0
        if rng is None:
            rng = random.Random()
        candidates = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) != self.start and (r, c) != self.end
        ]
        if not candidates:
            return 0
        count = max(1, round(len(candidates) * min(1.0, ratio)))
        rng.shuffle(candidates)
        chosen = candidates[:count]
        for r, c in chosen:
            self.weights[r][c] = mud_cost
        return len(chosen)

    def cell_id(self, r: int, c: int) -> int:
        """二维坐标 (r, c) 转为一维编号（0 ~ rows*cols-1），供并查集使用。O(1)。"""
        return r * self.cols + c

    def to_point(self, cell_id: int) -> tuple[int, int]:
        """一维编号转回二维坐标 (r, c)。O(1)。"""
        return cell_id // self.cols, cell_id % self.cols

    @classmethod
    def generate(
        cls,
        rows: int,
        cols: int,
        method: str = "kruskal",
        rng: random.Random | None = None,
        *,
        loop_ratio: float = 0.0,
        mud_ratio: float = 0.0,
    ) -> Maze:
        """工厂方法：按指定算法生成迷宫，并可选叠加随机拆环与带权泥地地形。"""
        if rng is None:
            rng = random.Random()
        if method == "kruskal":
            from maze.generators.kruskal import generate

            maze = generate(rows, cols, rng=rng)
        elif method == "prim":
            from maze.generators.prim import generate

            maze = generate(rows, cols, rng=rng)
        elif method == "backtracker":
            from maze.generators.recursive_backtracker import generate

            maze = generate(rows, cols, rng=rng)
        elif method == "division":
            from maze.generators.recursive_division import generate

            maze = generate(rows, cols, rng=rng)
        else:
            raise ValueError(f"Unknown generator: {method}")

        if loop_ratio > 0:
            maze.add_loops(loop_ratio, rng=rng)
        if mud_ratio > 0:
            maze.apply_weighted_terrain(mud_ratio, rng=rng)
        return maze
