"""基于 PySide6 (Qt) 的迷宫交互可视化模块。

提供完整交互流程：
1. 启动配置弹窗（StartupDialog）：询问迷宫行数、列数与生成算法（Kruskal / Prim）；
2. 自己试着走（ManualWalkState）：使用方向键或 WASD 亲自走迷宫，自动阻挡穿墙并统计步数；
3. 让程序走（BFS vs DFS 同屏对比）：左右并排展示同一个迷宫上的 BFS 与 DFS 求解过程，
   支持自动播放/暂停、速度调节、进度条拖动，以及使用方向键一步一步前进或回退。
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import sys
from typing import Callable

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QKeyEvent, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from maze.model import DELTA, E, Maze, N, S, SolveResult, W

# 迷宫绘制配色方案
BG_COLOR = QColor(242, 244, 247)
CELL_COLOR = QColor(250, 250, 246)
WALL_COLOR = QColor(42, 46, 54)
START_COLOR = QColor(72, 196, 118)
END_COLOR = QColor(232, 88, 88)

# 手动走迷宫配色
MANUAL_VISITED_COLOR = QColor(214, 234, 255)
MANUAL_TRAIL_COLOR = QColor(48, 130, 235)
PLAYER_COLOR = QColor(28, 100, 242)

# 算法求解动画配色
SOLVER_VISITED_COLOR = QColor(182, 214, 255)    # 浅蓝色：算法探索过的格子
ACTIVE_STACK_COLOR = QColor(148, 206, 255)      # 亮蓝色：当前还在递归栈上的活跃路径格
ACTIVE_LINE_COLOR = QColor(36, 114, 216)        # 深蓝色：当前递归调用链连线
BACKTRACKED_COLOR = QColor(224, 198, 212)       # 淡灰紫：确认走入死胡同并已回溯退出的格子
SOLVER_PATH_COLOR = QColor(255, 205, 68)        # 金黄色：最终求得的路径
SOLVER_PATH_LINE_COLOR = QColor(214, 126, 14)   # 橙棕色：最终路径中心连线
CURRENT_CURSOR_COLOR = QColor(255, 92, 34)      # 橙红色：当前步正在探索/描线的格子光标
BACKTRACK_CURSOR_COLOR = QColor(186, 48, 138)   # 紫红色：当前步正在死路回溯退出时的光标

# 迷宫生成动画配色
GEN_UNCARVED_COLOR = QColor(198, 208, 222)      # 冷灰石板底色：尚未被打通的未连通区域
GEN_ACTIVE_COLOR = QColor(110, 231, 183)        # 亮薄荷绿：当前步刚打通的两个相邻格
GEN_TRAIL_COLOR = QColor(186, 240, 222)         # 淡薄荷青：近期刚打通的走廊余晖过渡色
GEN_CURSOR_COLOR = QColor(16, 185, 129)         # 翠绿色：拆墙光晕涟漪与主火花
GEN_SPARK_COLOR = QColor(253, 224, 71)          # 暖金色：拆墙瞬间的火花点缀
GEN_TRAIL_LENGTH = 14                           # 余晖尾迹保留的最近拆墙/筑墙步数

# 递归分割法（筑墙）与带权泥地配色
DIV_ACTIVE_COLOR = QColor(199, 210, 254)        # 浅靛蓝：递归分割当前筑墙两侧格子
DIV_TRAIL_COLOR = QColor(224, 231, 255)         # 淡靛蓝：近期筑墙余晖
DIV_CURSOR_COLOR = QColor(79, 70, 229)          # 靛青色：筑墙生长光线与光晕
DIV_SPARK_COLOR = QColor(147, 197, 253)         # 天蓝色：筑墙火花点缀
MUD_COLOR = QColor(196, 168, 130)               # 暖棕泥地底色（高通行代价地形）
MUD_TINT_COLOR = QColor(168, 124, 72, 72)       # 泥地半透明覆层（避免被探索浅蓝完全遮盖）
MUD_BORDER_COLOR = QColor(146, 102, 56, 165)
MUD_TEXT_COLOR = QColor(92, 64, 38)


def _lerp_color(c1: QColor, c2: QColor, w: float) -> QColor:
    """按比例 w (0.0~1.0) 对两种颜色做线性插值，用于生成柔和的余晖过渡。"""
    t = max(0.0, min(1.0, w))
    return QColor(
        round(c1.red() + (c2.red() - c1.red()) * t),
        round(c1.green() + (c2.green() - c1.green()) * t),
        round(c1.blue() + (c2.blue() - c1.blue()) * t),
        round(c1.alpha() + (c2.alpha() - c1.alpha()) * t),
    )


class ManualWalkState:
    """“自己试着走”模式的状态机（纯逻辑，不依赖 Qt 界面，方便单元测试）。"""

    def __init__(self, maze: Maze) -> None:
        self.maze = maze
        self.pos: tuple[int, int] = maze.start
        self.trail: list[tuple[int, int]] = [maze.start]
        self.visited: set[tuple[int, int]] = {maze.start}
        self.steps: int = 0
        self.total_cost: int = 0
        self.reached_end: bool = maze.start == maze.end

    def move(self, direction: int) -> bool:
        """尝试向指定方向走一步；若撞墙或越界返回 False，成功移动返回 True。"""
        r, c = self.pos
        # 检查当前方向是否有墙，有墙绝对不能穿过去
        if self.maze.has_wall(r, c, direction):
            return False
        dr, dc = DELTA[direction]
        nr, nc = r + dr, c + dc
        if not self.maze.in_bounds(nr, nc):
            return False

        self.pos = (nr, nc)
        self.steps += 1
        self.total_cost += self.maze.cell_cost(nr, nc)
        self.visited.add(self.pos)

        # 如果玩家往回退了一格（回到轨迹倒数第二个格子），就把最后一格弹出，保持折返路线整洁
        if len(self.trail) >= 2 and self.trail[-2] == self.pos:
            self.trail.pop()
        else:
            self.trail.append(self.pos)

        self.reached_end = self.pos == self.maze.end
        return True

    def reset(self) -> None:
        """重置玩家位置、步数与累计代价，回到起点重新走。"""
        self.pos = self.maze.start
        self.trail = [self.maze.start]
        self.visited = {self.maze.start}
        self.steps = 0
        self.total_cost = 0
        self.reached_end = self.maze.start == self.maze.end


@dataclass(frozen=True)
class TimelineSnapshot:
    """某一离散步数下算法求解进度的渲染快照。"""

    clamped_step: int
    visited_count: int
    path_count: int
    current_cell: tuple[int, int] | None
    phase: str
    backtracked_cells: frozenset[tuple[int, int]] = frozenset()
    active_stack: tuple[tuple[int, int], ...] = ()
    current_action: str = ""
    backtrack_count: int = 0


class StepTimeline:
    """将求解结果 SolveResult 映射为可随时前进/回退的离散步进时间线。

    - 若 SolveResult.trace 非空（如递归版 DFS）：按 ("visit", cell) 与 ("backtrack", cell)
      真实重放每次深入探索与死路回溯退出，之后再逐格描出最终路径；
    - 若 SolveResult.trace 为空：按 visited_order 播放探索过程，再描出最终路径。
    """

    def __init__(self, result: SolveResult) -> None:
        self.result = result
        self.visited_total = len(result.visited_order)
        self.path_total = len(result.path)
        self.use_trace = bool(result.trace)
        self.search_total = len(result.trace) if self.use_trace else self.visited_total
        self.total_steps = self.search_total + self.path_total

    def snapshot(self, step: int) -> TimelineSnapshot:
        """根据步数 step 返回钳位后的进度快照，支持前进和回退到任意一步。"""
        clamped = max(0, min(step, self.total_steps))
        if clamped == 0:
            return TimelineSnapshot(0, 0, 0, None, "未开始")

        if self.use_trace:
            return self._snapshot_with_trace(clamped)

        # 无 trace 时的回放模式（队列版 BFS / 非递归 DFS / 按层递归 BFS）
        if clamped <= self.visited_total:
            return TimelineSnapshot(
                clamped_step=clamped,
                visited_count=clamped,
                path_count=0,
                current_cell=self.result.visited_order[clamped - 1],
                phase="搜索中",
                current_action="visit",
            )

        p_count = clamped - self.visited_total
        cur_cell = self.result.path[p_count - 1] if p_count > 0 else None
        phase = "已完成" if clamped == self.total_steps else "回溯路径"
        return TimelineSnapshot(
            clamped_step=clamped,
            visited_count=self.visited_total,
            path_count=p_count,
            current_cell=cur_cell,
            phase=phase,
            current_action="path",
        )

    def _snapshot_with_trace(self, clamped: int) -> TimelineSnapshot:
        """按 trace 事件流重放到第 clamped 步，还原探索格、活跃递归栈和已回溯死路格。"""
        event_limit = min(clamped, self.search_total)
        active_stack: list[tuple[int, int]] = []
        backtracked: set[tuple[int, int]] = set()
        visit_count = 0
        backtrack_count = 0
        last_action = ""
        last_cell: tuple[int, int] | None = None

        for action, cell in self.result.trace[:event_limit]:
            last_action = action
            last_cell = cell
            if action == "visit":
                visit_count += 1
                active_stack.append(cell)
            elif action == "backtrack":
                backtrack_count += 1
                if active_stack and active_stack[-1] == cell:
                    active_stack.pop()
                backtracked.add(cell)

        # 阶段 1：仍在搜索/回溯事件流中
        if clamped <= self.search_total:
            phase = "死路回溯" if last_action == "backtrack" else "搜索中"
            return TimelineSnapshot(
                clamped_step=clamped,
                visited_count=visit_count,
                path_count=0,
                current_cell=last_cell,
                phase=phase,
                backtracked_cells=frozenset(backtracked),
                active_stack=tuple(active_stack),
                current_action=last_action,
                backtrack_count=backtrack_count,
            )

        # 阶段 2：搜索结束，开始逐格高亮最终找到的路径
        p_count = clamped - self.search_total
        cur_cell = self.result.path[p_count - 1] if p_count > 0 else None
        phase = "已完成" if clamped == self.total_steps else "回溯路径"
        return TimelineSnapshot(
            clamped_step=clamped,
            visited_count=visit_count,
            path_count=p_count,
            current_cell=cur_cell,
            phase=phase,
            backtracked_cells=frozenset(backtracked),
            active_stack=tuple(active_stack),
            current_action="path",
            backtrack_count=backtrack_count,
        )


@dataclass(frozen=True)
class GenerationSnapshot:
    """迷宫生成动画在某一离散步数下的状态快照。"""

    clamped_step: int
    total_steps: int
    maze: Maze
    last_edge: tuple[tuple[int, int], tuple[int, int]] | None
    carved_cells: frozenset[tuple[int, int]]
    phase: str
    recent_edges: tuple[tuple[tuple[int, int], tuple[int, int]], ...] = ()
    last_action: str = "remove"
    recent_steps: tuple[tuple[str, tuple[int, int], tuple[int, int]], ...] = ()


class GenerationTimeline:
    """将 Maze.gen_steps / carve_history 映射为可随时前进/回退的迷宫生成时间线。"""

    def __init__(self, maze: Maze) -> None:
        self.source_maze = maze
        self._rows = maze.rows
        self._cols = maze.cols
        self._initial_open = maze.initial_open
        if maze.gen_steps:
            self._steps = list(maze.gen_steps)
        else:
            self._steps = [("remove", a, b) for a, b in maze.carve_history]
        self.total_steps = len(self._steps)
        self._cached_step = -1
        self._cached_maze: Maze | None = None
        self._cached_cells: set[tuple[int, int]] = set()

    def snapshot(self, step: int) -> GenerationSnapshot:
        """返回第 step 步拆墙或筑墙后的迷宫快照，支持顺序递增缓存与回退重建。"""
        clamped = max(0, min(step, self.total_steps))
        if self._cached_maze is None or clamped < self._cached_step:
            self._cached_maze = Maze(self._rows, self._cols)
            self._cached_maze.start = self.source_maze.start
            self._cached_maze.end = self.source_maze.end
            self._cached_maze.weights = [row[:] for row in self.source_maze.weights]
            if self._initial_open:
                self._cached_maze.clear_internal_walls()
            self._cached_cells = set()
            self._cached_step = 0

        while self._cached_step < clamped:
            action, a, b = self._steps[self._cached_step]
            if action == "add":
                self._cached_maze.add_wall_between(a, b)
            else:
                self._cached_maze.remove_wall_between(a, b)
            self._cached_cells.add(a)
            self._cached_cells.add(b)
            self._cached_step += 1

        # 返回独立拷贝，避免后续调用 snapshot() 时覆写之前持有快照中的 walls
        maze_copy = Maze(self._rows, self._cols)
        maze_copy.start = self._cached_maze.start
        maze_copy.end = self._cached_maze.end
        maze_copy.initial_open = self._initial_open
        maze_copy.walls = [row[:] for row in self._cached_maze.walls]
        maze_copy.weights = [row[:] for row in self._cached_maze.weights]

        last_step = self._steps[clamped - 1] if clamped > 0 else None
        last_action = last_step[0] if last_step is not None else ("add" if self._initial_open else "remove")
        last_edge = (last_step[1], last_step[2]) if last_step is not None else None
        recent_steps = tuple(self._steps[max(0, clamped - GEN_TRAIL_LENGTH) : clamped])
        recent_edges = tuple((a, b) for _, a, b in recent_steps)
        if clamped == 0:
            phase = "未开始"
        elif clamped == self.total_steps:
            phase = "已完成"
        else:
            phase = "生成中"

        return GenerationSnapshot(
            clamped_step=clamped,
            total_steps=self.total_steps,
            maze=maze_copy,
            last_edge=last_edge,
            carved_cells=frozenset(self._cached_cells),
            phase=phase,
            recent_edges=recent_edges,
            last_action=last_action,
            recent_steps=recent_steps,
        )


class MazeCanvas(QWidget):
    """自绘迷宫画布控件，会根据当前窗口大小自动缩放网格并居中绘制。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(280, 280)
        self._mode: str = "empty"
        self._maze: Maze | None = None
        self._walk_state: ManualWalkState | None = None
        self._result: SolveResult | None = None
        self._gen_timeline: GenerationTimeline | None = None
        self._step: int = 0
        self._gen_anim_t: float = 1.0

    def set_manual_state(self, maze: Maze, walk_state: ManualWalkState) -> None:
        """切换为“自己试着走”模式并刷新画面。"""
        self._mode = "manual"
        self._maze = maze
        self._walk_state = walk_state
        self._result = None
        self._gen_timeline = None
        self.update()

    def set_solver_state(self, maze: Maze, result: SolveResult, step: int) -> None:
        """切换为“算法步进展示”模式，并渲染到第 step 步的画面。"""
        self._mode = "solver"
        self._maze = maze
        self._walk_state = None
        self._result = result
        self._gen_timeline = None
        self._step = step
        self.update()

    def set_generation_state(
        self,
        timeline: GenerationTimeline,
        step: int,
        anim_t: float = 1.0,
    ) -> None:
        """切换为“迷宫生成动画”模式，渲染第 step 步的拆墙状态与过渡帧 anim_t (0.0~1.0)。"""
        self._mode = "generation"
        self._maze = timeline.source_maze
        self._walk_state = None
        self._result = None
        self._gen_timeline = timeline
        self._step = step
        self._gen_anim_t = max(0.0, min(1.0, anim_t))
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), BG_COLOR)

        if self._maze is None:
            return

        gen_snap: GenerationSnapshot | None = None
        if self._mode == "generation" and self._gen_timeline is not None:
            gen_snap = self._gen_timeline.snapshot(self._step)
            maze = gen_snap.maze
        else:
            maze = self._maze

        margin = 14.0
        avail_w = max(10.0, self.width() - 2 * margin)
        avail_h = max(10.0, self.height() - 2 * margin)
        # 取宽、高方向缩放比例的较小值，保证整个迷宫完整放进画布且格子保持正方形
        cell_px = max(4.0, min(avail_w / maze.cols, avail_h / maze.rows))
        maze_w = cell_px * maze.cols
        maze_h = cell_px * maze.rows
        ox = (self.width() - maze_w) / 2.0
        oy = (self.height() - maze_h) / 2.0

        if gen_snap is not None:
            self._paint_generation(painter, gen_snap, self._gen_anim_t, ox, oy, cell_px, maze_w, maze_h)
            if gen_snap.clamped_step == gen_snap.total_steps and gen_snap.total_steps > 0:
                self._paint_weights_overlay(painter, maze, ox, oy, cell_px, draw_base=True)
                self._paint_endpoints(painter, maze, ox, oy, cell_px)
            self._paint_walls(painter, maze, ox, oy, cell_px)
            self._paint_carving_fx(painter, gen_snap, self._gen_anim_t, ox, oy, cell_px)
            return

        # 1. 画迷宫整块底色与泥地地形底色
        painter.fillRect(QRectF(ox, oy, maze_w, maze_h), CELL_COLOR)
        self._paint_weights_base(painter, maze, ox, oy, cell_px)

        # 2. 按模式绘制格内状态（手动轨迹 或 算法搜索进度）
        if self._mode == "manual" and self._walk_state is not None:
            self._paint_manual(painter, maze, self._walk_state, ox, oy, cell_px)
        elif self._mode == "solver" and self._result is not None:
            self._paint_solver(painter, maze, self._result, self._step, ox, oy, cell_px)

        # 2.5 叠加泥地纹理/边框与代价值（避免被探索蓝完全掩盖）
        self._paint_weights_overlay(painter, maze, ox, oy, cell_px, draw_base=False)

        # 3. 绘制起点（绿）和终点（红）方块
        self._paint_endpoints(painter, maze, ox, oy, cell_px)

        # 4. 如果是手动模式，最后在最上层画玩家当前位置圆点，避免被起终点色块盖住
        if self._mode == "manual" and self._walk_state is not None:
            pr, pc = self._walk_state.pos
            cx = ox + (pc + 0.5) * cell_px
            cy = oy + (pr + 0.5) * cell_px
            radius = max(2.5, cell_px * 0.28)
            painter.setPen(QPen(Qt.white, max(1.0, cell_px * 0.07)))
            painter.setBrush(QBrush(PLAYER_COLOR))
            painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # 5. 最外层绘制四向位掩码墙壁
        self._paint_walls(painter, maze, ox, oy, cell_px)

    def _paint_generation(
        self,
        painter: QPainter,
        snap: GenerationSnapshot,
        anim_t: float,
        ox: float,
        oy: float,
        cell_px: float,
        maze_w: float,
        maze_h: float,
    ) -> None:
        """绘制迷宫生成动画帧底色：支持从全墙拆墙（冷灰底）与递归分割筑墙（米白底）。"""
        if snap.maze.initial_open:
            painter.fillRect(QRectF(ox, oy, maze_w, maze_h), CELL_COLOR)
        else:
            painter.fillRect(QRectF(ox, oy, maze_w, maze_h), GEN_UNCARVED_COLOR)
            for r, c in snap.carved_cells:
                painter.fillRect(
                    QRectF(ox + c * cell_px, oy + r * cell_px, cell_px, cell_px),
                    CELL_COLOR,
                )

        # 绘制最近几步留下的余晖（拆墙为薄荷绿，筑墙为淡靛蓝）
        recent_list = snap.recent_steps if snap.recent_steps else tuple(("remove", a, b) for a, b in snap.recent_edges)
        total_recent = len(recent_list)
        if total_recent > 0:
            for idx, (action, a, b) in enumerate(recent_list):
                w = (idx + 1) / total_recent
                target_trail = DIV_TRAIL_COLOR if action == "add" else GEN_TRAIL_COLOR
                trail_color = _lerp_color(CELL_COLOR, target_trail, w * 0.85)
                for r, c in (a, b):
                    painter.fillRect(
                        QRectF(ox + c * cell_px, oy + r * cell_px, cell_px, cell_px),
                        trail_color,
                    )

        # 最新一步在 anim_t 期间叠加呼吸脉冲
        if snap.last_edge is not None:
            ease = 1.0 - (1.0 - anim_t) ** 3
            pulse = 1.0 - 0.6 * ease
            base_t = DIV_TRAIL_COLOR if snap.last_action == "add" else GEN_TRAIL_COLOR
            peak_c = DIV_ACTIVE_COLOR if snap.last_action == "add" else GEN_ACTIVE_COLOR
            active_color = _lerp_color(base_t, peak_c, pulse)
            for r, c in snap.last_edge:
                painter.fillRect(
                    QRectF(ox + c * cell_px, oy + r * cell_px, cell_px, cell_px),
                    active_color,
                )

    def _paint_carving_fx(
        self,
        painter: QPainter,
        snap: GenerationSnapshot,
        anim_t: float,
        ox: float,
        oy: float,
        cell_px: float,
    ) -> None:
        """在墙线之上绘制精美拆墙/筑墙特效：壁面收缩或生长、径向光晕涟漪与火花微粒。"""
        if snap.last_edge is None:
            return

        a, b = snap.last_edge
        r1, c1 = a
        r2, c2 = b
        is_add = snap.last_action == "add"
        # 计算两格之间共享的那堵墙的精确线段端点
        if r1 == r2:
            wx1 = wx2 = ox + max(c1, c2) * cell_px
            wy1 = oy + r1 * cell_px
            wy2 = wy1 + cell_px
        else:
            wy1 = wy2 = oy + max(r1, r2) * cell_px
            wx1 = ox + c1 * cell_px
            wx2 = wx1 + cell_px

        mid_x = (wx1 + wx2) * 0.5
        mid_y = (wy1 + wy2) * 0.5
        cursor_base = DIV_CURSOR_COLOR if is_add else GEN_CURSOR_COLOR
        active_base = DIV_ACTIVE_COLOR if is_add else GEN_ACTIVE_COLOR
        spark_alt = DIV_SPARK_COLOR if is_add else GEN_SPARK_COLOR

        if 0.0 <= anim_t < 1.0:
            ease = 1.0 - (1.0 - anim_t) ** 3
            wall_w = max(1.4, min(3.0, cell_px * 0.1))
            hx = (wx2 - wx1) * 0.5
            hy = (wy2 - wy1) * 0.5

            if is_add:
                # 递归分割筑墙特效：先遮住完整墙线，再让新墙从中点向两端生长展开
                mask_color = _lerp_color(DIV_TRAIL_COLOR, DIV_ACTIVE_COLOR, 1.0 - 0.6 * ease)
                painter.setPen(QPen(mask_color, wall_w + 1.2, Qt.SolidLine, Qt.RoundCap))
                painter.drawLine(QLineF(wx1, wy1, wx2, wy2))
                if ease > 0.02:
                    grow_color = _lerp_color(DIV_CURSOR_COLOR, WALL_COLOR, ease * 0.85)
                    painter.setPen(QPen(grow_color, wall_w, Qt.SolidLine, Qt.RoundCap))
                    painter.drawLine(
                        QLineF(mid_x - hx * ease, mid_y - hy * ease, mid_x + hx * ease, mid_y + hy * ease)
                    )
            else:
                # 1. 双开门式墙壁收缩：残余墙段从中心向两端平滑退缩并渐隐
                rem = max(0.0, 1.0 - ease)
                if rem > 0.02:
                    fade_wall = QColor(WALL_COLOR)
                    fade_wall.setAlpha(int(255 * (1.0 - ease * 0.65)))
                    painter.setPen(QPen(fade_wall, wall_w, Qt.SolidLine, Qt.RoundCap))
                    painter.drawLine(QLineF(wx1, wy1, wx1 + hx * rem, wy1 + hy * rem))
                    painter.drawLine(QLineF(wx2, wy2, wx2 - hx * rem, wy2 - hy * rem))

            # 2. 墙中点径向光晕涟漪：柔和扩张并淡出
            radius = max(4.0, cell_px * (0.18 + 0.78 * ease))
            grad = QRadialGradient(QPointF(mid_x, mid_y), radius)
            alpha = int(175 * (1.0 - ease))
            c_center = QColor(cursor_base)
            c_center.setAlpha(alpha)
            c_mid = QColor(active_base)
            c_mid.setAlpha(int(alpha * 0.45))
            c_edge = QColor(cursor_base)
            c_edge.setAlpha(0)
            grad.setColorAt(0.0, c_center)
            grad.setColorAt(0.55, c_mid)
            grad.setColorAt(1.0, c_edge)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawEllipse(QPointF(mid_x, mid_y), radius, radius)

            # 3. 6 颗确定性飞散火花微粒（由格坐标决定方向，前进和回退完全可逆）
            base_angle = ((r1 * 73 + c1 * 139 + r2 * 37 + c2 * 97) % 360) * math.pi / 180.0
            for i in range(6):
                angle = base_angle + i * (math.pi / 3.0) + (0.18 if i % 2 == 0 else -0.15)
                dist = cell_px * (0.12 + (0.48 + 0.14 * (i % 2)) * ease)
                px = mid_x + math.cos(angle) * dist
                py = mid_y + math.sin(angle) * dist
                spark_r = max(1.0, cell_px * 0.08 * (1.0 - 0.6 * ease))
                spark_color = QColor(spark_alt if i % 2 == 0 else cursor_base)
                spark_color.setAlpha(int(230 * (1.0 - ease)))
                painter.setBrush(QBrush(spark_color))
                painter.drawEllipse(QPointF(px, py), spark_r, spark_r)

        # 生成进行中时为当前边两侧保留柔和边框，便于停步观察当前位置
        if snap.phase == "生成中":
            pad = max(1.0, cell_px * 0.1)
            frame_color = QColor(cursor_base)
            frame_color.setAlpha(int(200 if anim_t < 1.0 else 115))
            painter.setPen(QPen(frame_color, max(1.2, cell_px * 0.08), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(Qt.NoBrush)
            for r, c in (a, b):
                painter.drawRect(
                    QRectF(
                        ox + c * cell_px + pad,
                        oy + r * cell_px + pad,
                        max(2.0, cell_px - 2 * pad),
                        max(2.0, cell_px - 2 * pad),
                    )
                )

    def _paint_weights_base(
        self,
        painter: QPainter,
        maze: Maze,
        ox: float,
        oy: float,
        cell_px: float,
    ) -> None:
        """为高代价泥地格子填充暖棕底色。"""
        for r in range(maze.rows):
            for c in range(maze.cols):
                if maze.weights[r][c] > 1:
                    painter.fillRect(
                        QRectF(ox + c * cell_px, oy + r * cell_px, cell_px, cell_px),
                        MUD_COLOR,
                    )

    def _paint_weights_overlay(
        self,
        painter: QPainter,
        maze: Maze,
        ox: float,
        oy: float,
        cell_px: float,
        *,
        draw_base: bool,
    ) -> None:
        """绘制泥地半透明纹理与代价数字角标，确保探索色块覆盖后仍清晰可见。"""
        font = painter.font()
        font.setPointSizeF(max(6.0, min(10.0, cell_px * 0.34)))
        font.setBold(True)
        painter.setFont(font)
        pad = max(1.0, cell_px * 0.12)

        for r in range(maze.rows):
            for c in range(maze.cols):
                w = maze.weights[r][c]
                if w <= 1:
                    continue
                rect = QRectF(ox + c * cell_px, oy + r * cell_px, cell_px, cell_px)
                if draw_base:
                    painter.fillRect(rect, MUD_COLOR)
                else:
                    painter.fillRect(rect, MUD_TINT_COLOR)
                painter.setPen(QPen(MUD_BORDER_COLOR, max(1.0, cell_px * 0.06)))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(
                    QRectF(
                        rect.x() + pad,
                        rect.y() + pad,
                        max(2.0, cell_px - 2 * pad),
                        max(2.0, cell_px - 2 * pad),
                    )
                )
                if cell_px >= 16:
                    painter.setPen(MUD_TEXT_COLOR)
                    painter.drawText(rect, Qt.AlignCenter, str(w))

    def _paint_manual(
        self,
        painter: QPainter,
        maze: Maze,
        walk_state: ManualWalkState,
        ox: float,
        oy: float,
        cell_px: float,
    ) -> None:
        for r, c in walk_state.visited:
            painter.fillRect(
                QRectF(ox + c * cell_px, oy + r * cell_px, cell_px, cell_px),
                MANUAL_VISITED_COLOR,
            )

        if len(walk_state.trail) >= 2:
            pen = QPen(MANUAL_TRAIL_COLOR, max(2.0, cell_px * 0.22))
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            points = [
                QPointF(ox + (c + 0.5) * cell_px, oy + (r + 0.5) * cell_px)
                for r, c in walk_state.trail
            ]
            for p1, p2 in zip(points, points[1:]):
                painter.drawLine(QLineF(p1, p2))

    def _paint_solver(
        self,
        painter: QPainter,
        maze: Maze,
        result: SolveResult,
        step: int,
        ox: float,
        oy: float,
        cell_px: float,
    ) -> None:
        snap = StepTimeline(result).snapshot(step)

        # 1. 先画已探索过的格子（浅蓝底色）
        for r, c in result.visited_order[: snap.visited_count]:
            painter.fillRect(
                QRectF(ox + c * cell_px, oy + r * cell_px, cell_px, cell_px),
                SOLVER_VISITED_COLOR,
            )

        # 2. 若有递归回溯信息，把已退出的死路格涂成淡灰紫色，把当前递归调用栈涂成亮蓝色
        for r, c in snap.backtracked_cells:
            painter.fillRect(
                QRectF(ox + c * cell_px, oy + r * cell_px, cell_px, cell_px),
                BACKTRACKED_COLOR,
            )

        if snap.active_stack:
            for r, c in snap.active_stack:
                painter.fillRect(
                    QRectF(ox + c * cell_px, oy + r * cell_px, cell_px, cell_px),
                    ACTIVE_STACK_COLOR,
                )
            # 在搜索/回溯阶段画出当前正在试探的递归调用链连线
            if snap.path_count == 0 and len(snap.active_stack) >= 2:
                pen = QPen(ACTIVE_LINE_COLOR, max(2.0, cell_px * 0.18))
                pen.setCapStyle(Qt.RoundCap)
                pen.setJoinStyle(Qt.RoundJoin)
                painter.setPen(pen)
                stack_pts = [
                    QPointF(ox + (c + 0.5) * cell_px, oy + (r + 0.5) * cell_px)
                    for r, c in snap.active_stack
                ]
                for p1, p2 in zip(stack_pts, stack_pts[1:]):
                    painter.drawLine(QLineF(p1, p2))

        # 3. 再画最终路径格子和中心连线（金黄色）
        path_slice = result.path[: snap.path_count]
        for r, c in path_slice:
            painter.fillRect(
                QRectF(ox + c * cell_px, oy + r * cell_px, cell_px, cell_px),
                SOLVER_PATH_COLOR,
            )

        if len(path_slice) >= 2:
            pen = QPen(SOLVER_PATH_LINE_COLOR, max(2.0, cell_px * 0.2))
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            points = [
                QPointF(ox + (c + 0.5) * cell_px, oy + (r + 0.5) * cell_px)
                for r, c in path_slice
            ]
            for p1, p2 in zip(points, points[1:]):
                painter.drawLine(QLineF(p1, p2))

        # 4. 用光标框标出当前步位置：回溯时用紫红框，探索/描线时用橙红框
        if snap.current_cell is not None:
            cr, cc = snap.current_cell
            pad = max(1.5, cell_px * 0.14)
            is_bt = snap.current_action == "backtrack"
            cursor_color = BACKTRACK_CURSOR_COLOR if is_bt else CURRENT_CURSOR_COLOR
            fill_rgba = QColor(186, 48, 138, 95) if is_bt else QColor(255, 92, 34, 90)
            painter.setPen(QPen(cursor_color, max(1.5, cell_px * 0.14)))
            painter.setBrush(QBrush(fill_rgba))
            painter.drawRect(
                QRectF(
                    ox + cc * cell_px + pad,
                    oy + cr * cell_px + pad,
                    max(2.0, cell_px - 2 * pad),
                    max(2.0, cell_px - 2 * pad),
                )
            )

    def _paint_endpoints(
        self,
        painter: QPainter,
        maze: Maze,
        ox: float,
        oy: float,
        cell_px: float,
    ) -> None:
        pad = max(1.5, cell_px * 0.18)
        size = max(2.0, cell_px - 2 * pad)
        sr, sc = maze.start
        er, ec = maze.end
        painter.fillRect(
            QRectF(ox + sc * cell_px + pad, oy + sr * cell_px + pad, size, size),
            START_COLOR,
        )
        painter.fillRect(
            QRectF(ox + ec * cell_px + pad, oy + er * cell_px + pad, size, size),
            END_COLOR,
        )

    def _paint_walls(
        self,
        painter: QPainter,
        maze: Maze,
        ox: float,
        oy: float,
        cell_px: float,
    ) -> None:
        wall_w = max(1.2, min(2.8, cell_px * 0.09))
        pen = QPen(WALL_COLOR, wall_w, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)

        for r in range(maze.rows):
            y0 = oy + r * cell_px
            y1 = y0 + cell_px
            for c in range(maze.cols):
                x0 = ox + c * cell_px
                x1 = x0 + cell_px
                if maze.has_wall(r, c, N):
                    painter.drawLine(QLineF(x0, y0, x1, y0))
                if maze.has_wall(r, c, E):
                    painter.drawLine(QLineF(x1, y0, x1, y1))
                if maze.has_wall(r, c, S):
                    painter.drawLine(QLineF(x0, y1, x1, y1))
                if maze.has_wall(r, c, W):
                    painter.drawLine(QLineF(x0, y0, x0, y1))


class StartupDialog(QDialog):
    """程序启动时弹出的迷宫配置窗口：选择尺寸、生成算法、拆环比例与泥地地形比例。"""

    def __init__(
        self,
        generators: list[tuple[str, str, Callable[..., Maze]]],
        *,
        initial_rows: int = 15,
        initial_cols: int = 15,
        initial_gen: str = "kruskal",
        initial_loop_ratio: float = 0.0,
        initial_mud_ratio: float = 0.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("迷宫生成配置")
        self.setMinimumWidth(340)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.rows_spin = QSpinBox(self)
        self.rows_spin.setRange(2, 60)
        self.rows_spin.setValue(max(2, min(60, initial_rows)))

        self.cols_spin = QSpinBox(self)
        self.cols_spin.setRange(2, 60)
        self.cols_spin.setValue(max(2, min(60, initial_cols)))

        self.gen_combo = QComboBox(self)
        for key, label, _ in generators:
            self.gen_combo.addItem(label, userData=key)
        idx = self.gen_combo.findData(initial_gen)
        if idx >= 0:
            self.gen_combo.setCurrentIndex(idx)

        self.loop_spin = QSpinBox(self)
        self.loop_spin.setRange(0, 40)
        self.loop_spin.setSuffix("%")
        self.loop_spin.setValue(max(0, min(40, round(initial_loop_ratio * 100))))

        self.mud_spin = QSpinBox(self)
        self.mud_spin.setRange(0, 50)
        self.mud_spin.setSuffix("%")
        self.mud_spin.setValue(max(0, min(50, round(initial_mud_ratio * 100))))

        form.addRow("迷宫行数：", self.rows_spin)
        form.addRow("迷宫列数：", self.cols_spin)
        form.addRow("生成方式：", self.gen_combo)
        form.addRow("拆环比例（制造多路径）：", self.loop_spin)
        form.addRow("泥地比例（高代价=5）：", self.mud_spin)
        layout.addLayout(form)

        buttons = QDialogButtonBox(self)
        ok_btn = buttons.addButton("生成迷宫", QDialogButtonBox.AcceptRole)
        ok_btn.setDefault(True)
        buttons.addButton("取消", QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_config(self) -> tuple[int, int, str]:
        """返回用户选择的 (行数, 列数, 生成算法key)。"""
        return (
            self.rows_spin.value(),
            self.cols_spin.value(),
            str(self.gen_combo.currentData()),
        )

    def get_full_config(self) -> tuple[int, int, str, float, float]:
        """返回完整配置 (行数, 列数, 生成算法key, 拆环比例, 泥地比例)。"""
        return (
            self.rows_spin.value(),
            self.cols_spin.value(),
            str(self.gen_combo.currentData()),
            self.loop_spin.value() / 100.0,
            self.mud_spin.value() / 100.0,
        )


class MazeMainWindow(QMainWindow):
    """迷宫主窗口：支持生成动画、自己试着走、以及双算法同屏对比（BFS/DFS/Dijkstra/A*）。"""

    def __init__(
        self,
        maze: Maze,
        gen_key: str,
        generators: list[tuple[str, str, Callable[..., Maze]]],
        bfs_solvers: list[tuple[str, str, Callable[[Maze], SolveResult]]],
        dfs_solvers: list[tuple[str, str, Callable[[Maze], SolveResult]]],
        *,
        loop_ratio: float = 0.0,
        mud_ratio: float = 0.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("迷宫系统 - 生成动画 / 交互探索 / 算法对比")
        self.resize(1140, 720)
        # 让主窗口本身能接收键盘焦点，防止方向键被按钮或下拉框吞掉
        self.setFocusPolicy(Qt.StrongFocus)

        self._generators = {k: (lbl, fn) for k, lbl, fn in generators}
        self._generators_list = generators
        self._bfs_solvers = bfs_solvers
        self._dfs_solvers = dfs_solvers
        self._loop_ratio = loop_ratio
        self._mud_ratio = mud_ratio

        self._maze = maze
        self._gen_key = gen_key
        self._walk_state = ManualWalkState(maze)

        self._bfs_result = SolveResult()
        self._dfs_result = SolveResult()
        self._optimal_steps = 0
        self._optimal_cost = 0
        self._bfs_timeline = StepTimeline(self._bfs_result)
        self._dfs_timeline = StepTimeline(self._dfs_result)
        self._cur_step = 0
        self._max_step = 0
        self._playing = False

        self._gen_timeline = GenerationTimeline(maze)
        self._gen_step = 0
        self._gen_max_step = self._gen_timeline.total_steps
        self._gen_playing = False
        self._gen_anim_t = 1.0
        self._gen_single_anim = False

        # 自动播放定时器（对比模式与生成动画模式共用，按当前页分别推进）
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_tick)

        self._build_ui()
        self._recompute_solvers()
        self._sync_generation_slider()
        self._refresh_all()
        self.setFocus()

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(12, 10, 12, 10)
        root_layout.setSpacing(8)

        # ---- 1. 顶部工具栏 ----
        top_bar = QHBoxLayout()
        self.info_label = QLabel(self)
        self.info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        top_bar.addWidget(self.info_label)
        top_bar.addStretch(1)

        self.btn_mode_gen = QPushButton("生成动画", self)
        self.btn_mode_gen.setCheckable(True)
        self.btn_mode_gen.setFocusPolicy(Qt.NoFocus)
        self.btn_mode_gen.clicked.connect(lambda: self.switch_mode(2))

        self.btn_mode_manual = QPushButton("自己试着走", self)
        self.btn_mode_manual.setCheckable(True)
        self.btn_mode_manual.setChecked(True)
        self.btn_mode_manual.setFocusPolicy(Qt.NoFocus)
        self.btn_mode_manual.clicked.connect(lambda: self.switch_mode(0))

        self.btn_mode_compare = QPushButton("让程序走（算法同屏对比）", self)
        self.btn_mode_compare.setCheckable(True)
        self.btn_mode_compare.setFocusPolicy(Qt.NoFocus)
        self.btn_mode_compare.clicked.connect(lambda: self.switch_mode(1))

        self.btn_regen = QPushButton("重新生成", self)
        self.btn_regen.setFocusPolicy(Qt.NoFocus)
        self.btn_regen.clicked.connect(self.regenerate_same_config)

        self.btn_reconfig = QPushButton("重新配置...", self)
        self.btn_reconfig.setFocusPolicy(Qt.NoFocus)
        self.btn_reconfig.clicked.connect(self.reconfigure_maze)

        top_bar.addWidget(self.btn_mode_gen)
        top_bar.addWidget(self.btn_mode_manual)
        top_bar.addWidget(self.btn_mode_compare)
        top_bar.addSpacing(12)
        top_bar.addWidget(self.btn_regen)
        top_bar.addWidget(self.btn_reconfig)
        root_layout.addLayout(top_bar)

        # ---- 2. 中央堆叠页面（第 0 页手动，第 1 页双算法同屏对比） ----
        self.stack = QStackedWidget(self)
        root_layout.addWidget(self.stack, stretch=1)

        # 第 0 页：自己试着走
        manual_page = QWidget(self)
        manual_layout = QVBoxLayout(manual_page)
        manual_bar = QHBoxLayout()
        self.manual_status_label = QLabel(self)
        self.manual_hint_label = QLabel("使用方向键 或 W/A/S/D 移动（绿：起点，红：终点）", self)
        self.manual_hint_label.setStyleSheet("color: #555;")
        self.btn_reset_walk = QPushButton("回到起点", self)
        self.btn_reset_walk.setFocusPolicy(Qt.NoFocus)
        self.btn_reset_walk.clicked.connect(self.reset_manual_walk)

        manual_bar.addWidget(self.manual_status_label)
        manual_bar.addStretch(1)
        manual_bar.addWidget(self.manual_hint_label)
        manual_bar.addWidget(self.btn_reset_walk)
        manual_layout.addLayout(manual_bar)

        self.manual_win_banner = QLabel(self)
        self.manual_win_banner.setStyleSheet(
            "background: #d8f5e0; color: #166534; padding: 6px 10px; "
            "border-radius: 4px; font-weight: bold;"
        )
        self.manual_win_banner.setVisible(False)
        manual_layout.addWidget(self.manual_win_banner)

        self.manual_canvas = MazeCanvas(manual_page)
        manual_layout.addWidget(self.manual_canvas, stretch=1)
        self.stack.addWidget(manual_page)

        # 第 1 页：让程序走（BFS vs DFS 同屏对比）
        compare_page = QWidget(self)
        compare_layout = QVBoxLayout(compare_page)

        # 控制条第 1 行：算法版本切换 + 单步/播放控制 + 速度滑块
        ctrl_row1 = QHBoxLayout()
        ctrl_row1.addWidget(QLabel("左侧算法:", self))
        self.bfs_combo = QComboBox(self)
        self.bfs_combo.setFocusPolicy(Qt.NoFocus)
        for key, label, _ in self._bfs_solvers:
            self.bfs_combo.addItem(label, userData=key)
        self.bfs_combo.currentIndexChanged.connect(self._on_solver_variant_changed)
        ctrl_row1.addWidget(self.bfs_combo)

        ctrl_row1.addSpacing(8)
        ctrl_row1.addWidget(QLabel("右侧算法:", self))
        self.dfs_combo = QComboBox(self)
        self.dfs_combo.setFocusPolicy(Qt.NoFocus)
        for key, label, _ in self._dfs_solvers:
            self.dfs_combo.addItem(label, userData=key)
        self.dfs_combo.currentIndexChanged.connect(self._on_solver_variant_changed)
        ctrl_row1.addWidget(self.dfs_combo)

        ctrl_row1.addStretch(1)

        self.btn_to_start = QPushButton("⏮ 起点", self)
        self.btn_prev_step = QPushButton("◀ 回退一步", self)
        self.btn_play_pause = QPushButton("▶ 播放", self)
        self.btn_next_step = QPushButton("▶ 前进一步", self)
        self.btn_to_end = QPushButton("⏭ 终点", self)

        for btn in (
            self.btn_to_start,
            self.btn_prev_step,
            self.btn_play_pause,
            self.btn_next_step,
            self.btn_to_end,
        ):
            btn.setFocusPolicy(Qt.NoFocus)
            ctrl_row1.addWidget(btn)

        self.btn_to_start.clicked.connect(lambda: self._jump_to_step(0))
        self.btn_prev_step.clicked.connect(self.step_backward)
        self.btn_play_pause.clicked.connect(self.toggle_play)
        self.btn_next_step.clicked.connect(self.step_forward)
        self.btn_to_end.clicked.connect(lambda: self._jump_to_step(self._max_step))

        ctrl_row1.addSpacing(10)
        ctrl_row1.addWidget(QLabel("速度:", self))
        self.speed_slider = QSlider(Qt.Horizontal, self)
        self.speed_slider.setRange(1, 120)
        self.speed_slider.setValue(15)
        self.speed_slider.setFixedWidth(110)
        self.speed_slider.setFocusPolicy(Qt.NoFocus)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        self.speed_label = QLabel("15 步/秒", self)
        ctrl_row1.addWidget(self.speed_slider)
        ctrl_row1.addWidget(self.speed_label)
        compare_layout.addLayout(ctrl_row1)

        # 控制条第 2 行：全局步数进度条
        ctrl_row2 = QHBoxLayout()
        self.global_step_label = QLabel("全局步数: 0 / 0", self)
        self.step_slider = QSlider(Qt.Horizontal, self)
        self.step_slider.setRange(0, 0)
        self.step_slider.setFocusPolicy(Qt.NoFocus)
        self.step_slider.valueChanged.connect(self._on_slider_moved)
        ctrl_row2.addWidget(self.global_step_label)
        ctrl_row2.addWidget(self.step_slider, stretch=1)
        compare_layout.addLayout(ctrl_row2)

        # 左右等宽双迷宫对比区域
        split_row = QHBoxLayout()
        split_row.setSpacing(12)

        self.bfs_group = QGroupBox("左侧解法", self)
        bfs_box_layout = QVBoxLayout(self.bfs_group)
        self.bfs_info_label = QLabel(self)
        self.bfs_canvas = MazeCanvas(self.bfs_group)
        bfs_box_layout.addWidget(self.bfs_info_label)
        bfs_box_layout.addWidget(self.bfs_canvas, stretch=1)

        self.dfs_group = QGroupBox("右侧解法", self)
        dfs_box_layout = QVBoxLayout(self.dfs_group)
        self.dfs_info_label = QLabel(self)
        self.dfs_canvas = MazeCanvas(self.dfs_group)
        dfs_box_layout.addWidget(self.dfs_info_label)
        dfs_box_layout.addWidget(self.dfs_canvas, stretch=1)

        split_row.addWidget(self.bfs_group, stretch=1)
        split_row.addWidget(self.dfs_group, stretch=1)
        compare_layout.addLayout(split_row, stretch=1)

        compare_hint = QLabel(
            "快捷键：→ / ↓ 前进一步  |  ← / ↑ 回退一步  |  空格 播放/暂停  |  Home / End 起点/终点"
            "    图例：浅蓝=探索  亮蓝链=递归栈  灰紫=死路已回溯  金黄=路径  棕色5=泥地",
            self,
        )
        compare_hint.setStyleSheet("color: #555;")
        compare_layout.addWidget(compare_hint)

        self.stack.addWidget(compare_page)

        # 第 2 页：迷宫生成动画（逐堵拆墙过程回放）
        gen_page = QWidget(self)
        gen_layout = QVBoxLayout(gen_page)

        gen_ctrl1 = QHBoxLayout()
        self.gen_info_label = QLabel(self)
        gen_ctrl1.addWidget(self.gen_info_label)
        gen_ctrl1.addStretch(1)

        self.btn_gen_to_start = QPushButton("⏮ 起点", self)
        self.btn_gen_prev_step = QPushButton("◀ 回退一步", self)
        self.btn_gen_play_pause = QPushButton("▶ 播放", self)
        self.btn_gen_next_step = QPushButton("▶ 前进一步", self)
        self.btn_gen_to_end = QPushButton("⏭ 终点", self)

        for btn in (
            self.btn_gen_to_start,
            self.btn_gen_prev_step,
            self.btn_gen_play_pause,
            self.btn_gen_next_step,
            self.btn_gen_to_end,
        ):
            btn.setFocusPolicy(Qt.NoFocus)
            gen_ctrl1.addWidget(btn)

        self.btn_gen_to_start.clicked.connect(lambda: self._jump_gen_step(0))
        self.btn_gen_prev_step.clicked.connect(self.gen_step_backward)
        self.btn_gen_play_pause.clicked.connect(self.toggle_gen_play)
        self.btn_gen_next_step.clicked.connect(self.gen_step_forward)
        self.btn_gen_to_end.clicked.connect(lambda: self._jump_gen_step(self._gen_max_step))

        gen_ctrl1.addSpacing(10)
        gen_ctrl1.addWidget(QLabel("速度:", self))
        self.gen_speed_slider = QSlider(Qt.Horizontal, self)
        self.gen_speed_slider.setRange(1, 200)
        self.gen_speed_slider.setValue(18)
        self.gen_speed_slider.setFixedWidth(120)
        self.gen_speed_slider.setFocusPolicy(Qt.NoFocus)
        self.gen_speed_slider.valueChanged.connect(self._on_gen_speed_changed)
        self.gen_speed_label = QLabel("18 步/秒", self)
        gen_ctrl1.addWidget(self.gen_speed_slider)
        gen_ctrl1.addWidget(self.gen_speed_label)
        gen_layout.addLayout(gen_ctrl1)

        gen_ctrl2 = QHBoxLayout()
        self.gen_step_label = QLabel("拆墙进度: 0 / 0", self)
        self.gen_step_slider = QSlider(Qt.Horizontal, self)
        self.gen_step_slider.setRange(0, 0)
        self.gen_step_slider.setFocusPolicy(Qt.NoFocus)
        self.gen_step_slider.valueChanged.connect(self._on_gen_slider_moved)
        gen_ctrl2.addWidget(self.gen_step_label)
        gen_ctrl2.addWidget(self.gen_step_slider, stretch=1)
        gen_layout.addLayout(gen_ctrl2)

        self.gen_canvas = MazeCanvas(gen_page)
        gen_layout.addWidget(self.gen_canvas, stretch=1)

        gen_hint = QLabel(
            "快捷键：→ / ↓ 下一堵墙  |  ← / ↑ 上一堵墙  |  空格 播放/暂停  |  Home / End 起点/终点"
            "    图例：冷灰=未开凿  薄荷=拆墙  靛蓝=筑墙（递归分割）  棕色5=泥地",
            self,
        )
        gen_hint.setStyleSheet("color: #555;")
        gen_layout.addWidget(gen_hint)

        self.stack.addWidget(gen_page)

    def switch_mode(self, mode_index: int) -> None:
        """在“自己试着走(0)”、“让程序走(1)”和“生成动画(2)”之间切换。"""
        self._stop_playback()
        self.stack.setCurrentIndex(mode_index)
        self.btn_mode_manual.setChecked(mode_index == 0)
        self.btn_mode_compare.setChecked(mode_index == 1)
        self.btn_mode_gen.setChecked(mode_index == 2)
        self._refresh_all()
        self.setFocus()

    def start_generation_animation(self) -> None:
        """切到生成动画页面并从第 0 步开始 60 FPS 自动播放拆墙过程。"""
        self.switch_mode(2)
        self._gen_step = 0
        self._gen_anim_t = 1.0
        self._refresh_generation()
        self.toggle_gen_play()

    def reset_manual_walk(self) -> None:
        """让手动走迷宫的玩家回到起点。"""
        self._walk_state.reset()
        self._refresh_manual()
        self.setFocus()

    def _build_maze_with_options(
        self,
        rows: int,
        cols: int,
        gen_key: str,
        loop_ratio: float,
        mud_ratio: float,
    ) -> Maze:
        _, gen_fn = self._generators[gen_key]
        new_maze = gen_fn(rows, cols)
        if loop_ratio > 0:
            new_maze.add_loops(loop_ratio)
        if mud_ratio > 0:
            new_maze.apply_weighted_terrain(mud_ratio)
        return new_maze

    def regenerate_same_config(self) -> None:
        """按当前尺寸、生成算法、拆环比例和泥地比例重新生成迷宫。"""
        was_gen = self.stack.currentIndex() == 2
        new_maze = self._build_maze_with_options(
            self._maze.rows,
            self._maze.cols,
            self._gen_key,
            self._loop_ratio,
            self._mud_ratio,
        )
        self._set_new_maze(new_maze, self._gen_key)
        if was_gen:
            self.start_generation_animation()

    def reconfigure_maze(self) -> None:
        """弹出配置对话框，重新选择尺寸、生成方式及拆环/泥地比例。"""
        was_gen = self.stack.currentIndex() == 2
        self._stop_playback()
        dlg = StartupDialog(
            self._generators_list,
            initial_rows=self._maze.rows,
            initial_cols=self._maze.cols,
            initial_gen=self._gen_key,
            initial_loop_ratio=self._loop_ratio,
            initial_mud_ratio=self._mud_ratio,
            parent=self,
        )
        if dlg.exec() == QDialog.Accepted:
            rows, cols, gen_key, loop_ratio, mud_ratio = dlg.get_full_config()
            self._loop_ratio = loop_ratio
            self._mud_ratio = mud_ratio
            new_maze = self._build_maze_with_options(rows, cols, gen_key, loop_ratio, mud_ratio)
            self._set_new_maze(new_maze, gen_key)
            if was_gen:
                self.start_generation_animation()
        self.setFocus()

    def _set_new_maze(self, maze: Maze, gen_key: str) -> None:
        self._stop_playback()
        self._maze = maze
        self._gen_key = gen_key
        self._walk_state = ManualWalkState(maze)
        self._gen_timeline = GenerationTimeline(maze)
        self._gen_max_step = self._gen_timeline.total_steps
        self._gen_step = 0
        self._gen_anim_t = 1.0
        self._sync_generation_slider()
        self._recompute_solvers()
        self._refresh_all()

    def _sync_generation_slider(self) -> None:
        self.gen_step_slider.blockSignals(True)
        self.gen_step_slider.setRange(0, self._gen_max_step)
        self.gen_step_slider.setValue(self._gen_step)
        self.gen_step_slider.blockSignals(False)

    def _recompute_solvers(self) -> None:
        """根据当前选择的左右算法重新求解，并计算全局最短步数/最优代价供参考。"""
        bfs_idx = max(0, self.bfs_combo.currentIndex())
        dfs_idx = max(0, self.dfs_combo.currentIndex())
        _, _, bfs_fn = self._bfs_solvers[bfs_idx]
        _, _, dfs_fn = self._dfs_solvers[dfs_idx]

        self._bfs_result = bfs_fn(self._maze)
        self._dfs_result = dfs_fn(self._maze)
        self._bfs_timeline = StepTimeline(self._bfs_result)
        self._dfs_timeline = StepTimeline(self._dfs_result)
        self._max_step = max(self._bfs_timeline.total_steps, self._dfs_timeline.total_steps)
        self._cur_step = 0

        solver_lookup = {k: fn for k, _, fn in self._bfs_solvers + self._dfs_solvers}
        ref_step_res = solver_lookup["bfs_queue"](self._maze) if "bfs_queue" in solver_lookup else self._bfs_result
        if "dijkstra" in solver_lookup:
            ref_cost_res = solver_lookup["dijkstra"](self._maze)
        elif "astar" in solver_lookup:
            ref_cost_res = solver_lookup["astar"](self._maze)
        else:
            ref_cost_res = ref_step_res
        self._optimal_steps = max(0, len(ref_step_res.path) - 1)
        self._optimal_cost = ref_cost_res.cost

        self.step_slider.blockSignals(True)
        self.step_slider.setRange(0, self._max_step)
        self.step_slider.setValue(0)
        self.step_slider.blockSignals(False)

    def _on_solver_variant_changed(self) -> None:
        self._stop_playback()
        self._recompute_solvers()
        self._refresh_compare()
        self.setFocus()

    def _on_slider_moved(self, value: int) -> None:
        self._stop_playback()
        self._cur_step = max(0, min(value, self._max_step))
        self._refresh_compare()

    def _on_speed_changed(self, value: int) -> None:
        self.speed_label.setText(f"{value} 步/秒")
        if self._playing:
            self._timer.start(max(10, int(1000 / value)))

    def _jump_to_step(self, step: int) -> None:
        self._stop_playback()
        self._cur_step = max(0, min(step, self._max_step))
        self._refresh_compare()

    def step_forward(self) -> None:
        """手动前进一步（若正在自动播放则先暂停）。"""
        self._stop_playback()
        if self._cur_step < self._max_step:
            self._cur_step += 1
            self._refresh_compare()

    def step_backward(self) -> None:
        """手动回退一步（若正在自动播放则先暂停）。"""
        self._stop_playback()
        if self._cur_step > 0:
            self._cur_step -= 1
            self._refresh_compare()

    def toggle_play(self) -> None:
        """切换自动播放与暂停状态。"""
        if self._playing:
            self._stop_playback()
        else:
            # 如果已经在终点步数，再次点击播放则从第 0 步重新开始放
            if self._cur_step >= self._max_step:
                self._cur_step = 0
                self._refresh_compare()
            self._playing = True
            self.btn_play_pause.setText("⏸ 暂停")
            interval_ms = max(10, int(1000 / max(1, self.speed_slider.value())))
            self._timer.start(interval_ms)

    def _stop_playback(self) -> None:
        self._playing = False
        self._gen_playing = False
        self._gen_single_anim = False
        self._gen_anim_t = 1.0
        self._timer.stop()
        if hasattr(self, "btn_play_pause"):
            self.btn_play_pause.setText("▶ 播放")
        if hasattr(self, "btn_gen_play_pause"):
            self.btn_gen_play_pause.setText("▶ 播放")

    def _on_gen_slider_moved(self, value: int) -> None:
        self._stop_playback()
        self._gen_step = max(0, min(value, self._gen_max_step))
        self._gen_anim_t = 1.0
        self._refresh_generation()

    def _on_gen_speed_changed(self, value: int) -> None:
        self.gen_speed_label.setText(f"{value} 步/秒")

    def _jump_gen_step(self, step: int) -> None:
        self._stop_playback()
        self._gen_step = max(0, min(step, self._gen_max_step))
        self._gen_anim_t = 1.0
        self._refresh_generation()

    def gen_step_forward(self) -> None:
        """生成动画手动前进一堵墙，并播放约 180 ms 的平滑拆墙缓动。"""
        self._stop_playback()
        if self._gen_step < self._gen_max_step:
            self._gen_step += 1
            self._gen_anim_t = 0.0
            self._gen_single_anim = True
            self._refresh_generation()
            self._timer.start(16)

    def gen_step_backward(self) -> None:
        """生成动画手动回退恢复一堵墙。"""
        self._stop_playback()
        if self._gen_step > 0:
            self._gen_step -= 1
            self._gen_anim_t = 1.0
            self._refresh_generation()

    def toggle_gen_play(self) -> None:
        """切换生成动画 60 FPS 自动播放与暂停。"""
        if self._gen_playing:
            self._stop_playback()
            self._refresh_generation()
        else:
            if self._gen_step >= self._gen_max_step:
                self._gen_step = 0
            self._gen_single_anim = False
            if self._gen_step < self._gen_max_step:
                self._gen_step += 1
                self._gen_anim_t = 0.0
            else:
                self._gen_anim_t = 1.0
            self._gen_playing = True
            self.btn_gen_play_pause.setText("⏸ 暂停")
            self._refresh_generation()
            self._timer.start(16)

    def _on_timer_tick(self) -> None:
        if self._gen_playing:
            speed = max(1, self.gen_speed_slider.value())
            self._gen_anim_t += speed / 60.0
            if self._gen_anim_t >= 1.0:
                advance = int(self._gen_anim_t)
                self._gen_anim_t -= advance
                if self._gen_step + advance <= self._gen_max_step:
                    self._gen_step += advance
                else:
                    self._gen_step = self._gen_max_step
                    self._stop_playback()
            self._refresh_generation()
        elif self._gen_single_anim:
            self._gen_anim_t += 16.0 / 180.0
            if self._gen_anim_t >= 1.0:
                self._gen_anim_t = 1.0
                self._gen_single_anim = False
                self._timer.stop()
            self._refresh_generation()
        elif self._playing:
            if self._cur_step < self._max_step:
                self._cur_step += 1
                self._refresh_compare()
            else:
                self._stop_playback()

    def _refresh_all(self) -> None:
        gen_label, _ = self._generators[self._gen_key]
        extras = []
        if self._loop_ratio > 0:
            extras.append(f"拆环：{round(self._loop_ratio * 100)}%")
        if self._mud_ratio > 0 or self._maze.has_weighted_terrain():
            extras.append(f"泥地：{round(self._mud_ratio * 100)}%" if self._mud_ratio > 0 else "带权地形")
        extra_text = f"  |  {'  |  '.join(extras)}" if extras else ""
        self.info_label.setText(
            f"当前迷宫：{self._maze.rows} × {self._maze.cols}  |  生成方式：{gen_label}{extra_text}"
        )
        self._refresh_manual()
        self._refresh_compare()
        self._refresh_generation()

    def _refresh_generation(self) -> None:
        gen_label, _ = self._generators[self._gen_key]
        snap = self._gen_timeline.snapshot(self._gen_step)
        verb = "筑墙" if self._maze.initial_open else "拆墙"
        self.gen_step_label.setText(f"{verb}进度: {snap.clamped_step} / {snap.total_steps}")
        self.gen_step_slider.blockSignals(True)
        self.gen_step_slider.setValue(snap.clamped_step)
        self.gen_step_slider.blockSignals(False)
        self.gen_info_label.setText(
            f"生成方式：{gen_label}  |  状态：{snap.phase}  |  已{verb}：{snap.clamped_step}/{snap.total_steps}"
        )
        self.gen_canvas.set_generation_state(self._gen_timeline, self._gen_step, self._gen_anim_t)

    def _refresh_manual(self) -> None:
        has_mud = self._maze.has_weighted_terrain()
        cost_part = (
            f"  |  累计代价: {self._walk_state.total_cost}（最优: {self._optimal_cost}）"
            if has_mud
            else ""
        )
        self.manual_status_label.setText(
            f"当前位置: {self._walk_state.pos}  |  已走步数: {self._walk_state.steps}  |  最短步数: {self._optimal_steps}{cost_part}"
        )
        if self._walk_state.reached_end:
            win_cost = (
                f"，累计代价 {self._walk_state.total_cost}（最优代价 {self._optimal_cost}）"
                if has_mud
                else ""
            )
            self.manual_win_banner.setText(
                f"恭喜到达终点！你用了 {self._walk_state.steps} 步{win_cost}（最少步数 {self._optimal_steps} 步）。"
            )
            self.manual_win_banner.setVisible(True)
        else:
            self.manual_win_banner.setVisible(False)
        self.manual_canvas.set_manual_state(self._maze, self._walk_state)

    def _refresh_compare(self) -> None:
        self.global_step_label.setText(f"全局步数: {self._cur_step} / {self._max_step}")
        self.step_slider.blockSignals(True)
        self.step_slider.setValue(self._cur_step)
        self.step_slider.blockSignals(False)

        bfs_idx = max(0, self.bfs_combo.currentIndex())
        dfs_idx = max(0, self.dfs_combo.currentIndex())
        self.bfs_group.setTitle(f"左侧：{self._bfs_solvers[bfs_idx][1]}")
        self.dfs_group.setTitle(f"右侧：{self._dfs_solvers[dfs_idx][1]}")

        bfs_snap = self._bfs_timeline.snapshot(self._cur_step)
        dfs_snap = self._dfs_timeline.snapshot(self._cur_step)

        bfs_bt = f"  |  已回溯：{bfs_snap.backtrack_count}" if self._bfs_timeline.use_trace else ""
        dfs_bt = f"  |  已回溯：{dfs_snap.backtrack_count}" if self._dfs_timeline.use_trace else ""
        self.bfs_info_label.setText(
            f"状态：{bfs_snap.phase}  |  进度：{bfs_snap.clamped_step}/{self._bfs_timeline.total_steps}"
            f"{bfs_bt}  |  扩展：{self._bfs_result.expanded}  |  路径长：{len(self._bfs_result.path)}"
            f"  |  代价：{self._bfs_result.cost}"
        )
        self.dfs_info_label.setText(
            f"状态：{dfs_snap.phase}  |  进度：{dfs_snap.clamped_step}/{self._dfs_timeline.total_steps}"
            f"{dfs_bt}  |  扩展：{self._dfs_result.expanded}  |  路径长：{len(self._dfs_result.path)}"
            f"  |  代价：{self._dfs_result.cost}"
        )

        self.bfs_canvas.set_solver_state(self._maze, self._bfs_result, self._cur_step)
        self.dfs_canvas.set_solver_state(self._maze, self._dfs_result, self._cur_step)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        if self.stack.currentIndex() == 0:
            # 手动走迷宫模式：上下左右 / WASD 移动
            dir_map = {
                Qt.Key_Up: N,
                Qt.Key_W: N,
                Qt.Key_Right: E,
                Qt.Key_D: E,
                Qt.Key_Down: S,
                Qt.Key_S: S,
                Qt.Key_Left: W,
                Qt.Key_A: W,
            }
            if key in dir_map:
                if self._walk_state.move(dir_map[key]):
                    self._refresh_manual()
                event.accept()
                return
        elif self.stack.currentIndex() == 1:
            # 程序演示模式：方向键控制单步前进与单步回退，空格控制播放/暂停
            if key in (Qt.Key_Right, Qt.Key_Down):
                self.step_forward()
                event.accept()
                return
            if key in (Qt.Key_Left, Qt.Key_Up):
                self.step_backward()
                event.accept()
                return
            if key == Qt.Key_Space:
                self.toggle_play()
                event.accept()
                return
            if key == Qt.Key_Home:
                self._jump_to_step(0)
                event.accept()
                return
            if key == Qt.Key_End:
                self._jump_to_step(self._max_step)
                event.accept()
                return
        elif self.stack.currentIndex() == 2:
            # 生成动画模式：方向键控制拆下一堵墙与回退上一堵墙
            if key in (Qt.Key_Right, Qt.Key_Down):
                self.gen_step_forward()
                event.accept()
                return
            if key in (Qt.Key_Left, Qt.Key_Up):
                self.gen_step_backward()
                event.accept()
                return
            if key == Qt.Key_Space:
                self.toggle_gen_play()
                event.accept()
                return
            if key == Qt.Key_Home:
                self._jump_gen_step(0)
                event.accept()
                return
            if key == Qt.Key_End:
                self._jump_gen_step(self._gen_max_step)
                event.accept()
                return

        super().keyPressEvent(event)


def run_app(
    generators: list[tuple[str, str, Callable[..., Maze]]],
    bfs_solvers: list[tuple[str, str, Callable[[Maze], SolveResult]]],
    dfs_solvers: list[tuple[str, str, Callable[[Maze], SolveResult]]],
    *,
    initial_rows: int = 15,
    initial_cols: int = 15,
    initial_gen: str = "kruskal",
    initial_loop_ratio: float = 0.0,
    initial_mud_ratio: float = 0.0,
) -> int:
    """启动 Qt 图形界面：先弹出配置框询问尺寸、生成算法与含环/地形比例，再进入主窗口。"""
    app = QApplication.instance() or QApplication(sys.argv)

    # 第一步：启动先询问用户要生成几乘几、选哪个生成方式及地形配置
    dialog = StartupDialog(
        generators,
        initial_rows=initial_rows,
        initial_cols=initial_cols,
        initial_gen=initial_gen,
        initial_loop_ratio=initial_loop_ratio,
        initial_mud_ratio=initial_mud_ratio,
    )
    if dialog.exec() != QDialog.Accepted:
        return 0

    rows, cols, gen_key, loop_ratio, mud_ratio = dialog.get_full_config()
    gen_map = {k: fn for k, _, fn in generators}
    maze = gen_map[gen_key](rows, cols)
    if loop_ratio > 0:
        maze.add_loops(loop_ratio)
    if mud_ratio > 0:
        maze.apply_weighted_terrain(mud_ratio)

    # 第二步：打开主窗口并自动从第 0 步开始播放迷宫生成动画
    window = MazeMainWindow(
        maze,
        gen_key,
        generators,
        bfs_solvers,
        dfs_solvers,
        loop_ratio=loop_ratio,
        mud_ratio=mud_ratio,
    )
    window.start_generation_animation()
    window.show()
    return app.exec()
