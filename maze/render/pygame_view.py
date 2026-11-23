"""Pygame 回放式动画渲染与交互界面（算法通过回调注入，渲染层保持零算法依赖）。"""
from __future__ import annotations

from typing import Callable

import pygame

from maze.model import E, Maze, N, S, SolveResult, W

WALL_COLOR = (40, 40, 40)
CELL_COLOR = (245, 245, 240)
PATH_COLOR = (255, 200, 60)
VISITED_COLOR = (180, 210, 255)
START_COLOR = (80, 200, 120)
END_COLOR = (230, 90, 90)

HUD_HEIGHT = 58
HUD_BG_COLOR = (30, 32, 38)
HUD_TEXT_COLOR = (235, 238, 245)
HUD_HINT_COLOR = (165, 175, 190)
MIN_WINDOW_WIDTH = 620
SPEED_LEVELS = (5, 15, 30, 60, 120, 240, 600, 1200)
DEFAULT_SPEED_INDEX = 3  # 60 格/秒


class ReplayState:
    """回放动画状态机，独立于 Pygame 主循环以便测试。"""

    def __init__(
        self,
        result: SolveResult | None = None,
        *,
        animate: bool = True,
        speed_idx: int = DEFAULT_SPEED_INDEX,
    ) -> None:
        self.speed_idx = max(0, min(speed_idx, len(SPEED_LEVELS) - 1))
        self.visited_total = 0
        self.path_total = 0
        self.visited_idx = 0
        self.path_idx = 0
        self.paused = False
        self._accum = 0.0
        self.reset(result, animate=animate)

    @property
    def speed(self) -> int:
        return SPEED_LEVELS[self.speed_idx]

    @property
    def is_finished(self) -> bool:
        return self.visited_idx >= self.visited_total and self.path_idx >= self.path_total

    def reset(self, result: SolveResult | None, *, animate: bool = True) -> None:
        self.visited_total = len(result.visited_order) if result is not None else 0
        self.path_total = len(result.path) if result is not None else 0
        self.paused = False
        self._accum = 0.0
        if animate:
            self.visited_idx = 0
            self.path_idx = 0
        else:
            self.visited_idx = self.visited_total
            self.path_idx = self.path_total

    def finish_immediately(self) -> None:
        self.visited_idx = self.visited_total
        self.path_idx = self.path_total
        self.paused = False
        self._accum = 0.0

    def advance(self, dt: float) -> None:
        """按时间步长 dt 推进回放：先显示访问序列，再逐格绘制路径。"""
        if self.paused or self.is_finished or dt <= 0:
            return
        self._accum += self.speed * dt
        steps = int(self._accum)
        if steps <= 0:
            return
        self._accum -= steps

        if self.visited_idx < self.visited_total:
            take = min(steps, self.visited_total - self.visited_idx)
            self.visited_idx += take
            steps -= take
        if steps > 0 and self.path_idx < self.path_total:
            take = min(steps, self.path_total - self.path_idx)
            self.path_idx += take

    def speed_up(self) -> None:
        if self.speed_idx < len(SPEED_LEVELS) - 1:
            self.speed_idx += 1

    def speed_down(self) -> None:
        if self.speed_idx > 0:
            self.speed_idx -= 1

    def toggle_pause(self) -> None:
        self.paused = not self.paused


def draw_maze(
    surface: pygame.Surface,
    maze: Maze,
    result: SolveResult | None = None,
    *,
    cell_px: int = 24,
    offset_x: int = 1,
    offset_y: int = 1,
    visited_count: int | None = None,
    path_count: int | None = None,
) -> None:
    """绘制迷宫底格、已访问节点、求解路径以及四向墙线。"""
    maze_rect = pygame.Rect(offset_x, offset_y, maze.cols * cell_px, maze.rows * cell_px)
    pygame.draw.rect(surface, CELL_COLOR, maze_rect)

    if result is not None:
        v_limit = len(result.visited_order) if visited_count is None else max(0, visited_count)
        for r, c in result.visited_order[:v_limit]:
            rect = pygame.Rect(offset_x + c * cell_px, offset_y + r * cell_px, cell_px, cell_px)
            pygame.draw.rect(surface, VISITED_COLOR, rect)

        p_limit = len(result.path) if path_count is None else max(0, path_count)
        path_slice = result.path[:p_limit]
        for r, c in path_slice:
            rect = pygame.Rect(offset_x + c * cell_px, offset_y + r * cell_px, cell_px, cell_px)
            pygame.draw.rect(surface, PATH_COLOR, rect)

        if len(path_slice) >= 2:
            points = [
                (
                    offset_x + c * cell_px + cell_px // 2,
                    offset_y + r * cell_px + cell_px // 2,
                )
                for r, c in path_slice
            ]
            line_w = max(2, cell_px // 5)
            pygame.draw.lines(surface, (215, 130, 15), False, points, line_w)

    sr, sc = maze.start
    er, ec = maze.end
    pad = max(2, cell_px // 6)
    start_rect = pygame.Rect(
        offset_x + sc * cell_px + pad,
        offset_y + sr * cell_px + pad,
        max(2, cell_px - 2 * pad),
        max(2, cell_px - 2 * pad),
    )
    end_rect = pygame.Rect(
        offset_x + ec * cell_px + pad,
        offset_y + er * cell_px + pad,
        max(2, cell_px - 2 * pad),
        max(2, cell_px - 2 * pad),
    )
    pygame.draw.rect(surface, START_COLOR, start_rect)
    pygame.draw.rect(surface, END_COLOR, end_rect)

    wall_w = 2
    for r in range(maze.rows):
        y0 = offset_y + r * cell_px
        y1 = y0 + cell_px
        for c in range(maze.cols):
            x0 = offset_x + c * cell_px
            x1 = x0 + cell_px
            if maze.has_wall(r, c, N):
                pygame.draw.line(surface, WALL_COLOR, (x0, y0), (x1, y0), wall_w)
            if maze.has_wall(r, c, E):
                pygame.draw.line(surface, WALL_COLOR, (x1, y0), (x1, y1), wall_w)
            if maze.has_wall(r, c, S):
                pygame.draw.line(surface, WALL_COLOR, (x0, y1), (x1, y1), wall_w)
            if maze.has_wall(r, c, W):
                pygame.draw.line(surface, WALL_COLOR, (x0, y0), (x0, y1), wall_w)


def draw_hud(
    surface: pygame.Surface,
    hud_rect: pygame.Rect,
    line1: str,
    line2: str,
    font: pygame.font.Font,
) -> None:
    """绘制底部状态栏（使用 ASCII 文本以兼容默认字体）。"""
    pygame.draw.rect(surface, HUD_BG_COLOR, hud_rect)
    surf1 = font.render(line1, True, HUD_TEXT_COLOR)
    surf2 = font.render(line2, True, HUD_HINT_COLOR)
    surface.blit(surf1, (hud_rect.x + 12, hud_rect.y + 8))
    surface.blit(surf2, (hud_rect.x + 12, hud_rect.y + 32))


def run(
    maze: Maze,
    result: SolveResult | None = None,
    cell_px: int = 24,
    fps: int = 60,
    *,
    animate: bool = True,
    title: str = "Maze Visualizer",
    status_text: str = "",
    on_regenerate: Callable[[], tuple[Maze, SolveResult | None, str]] | None = None,
    on_switch_solver: Callable[[Maze], tuple[SolveResult | None, str]] | None = None,
    on_switch_generator: Callable[[], tuple[Maze, SolveResult | None, str]] | None = None,
) -> None:
    """启动 Pygame 窗口，回放求解动画并响应键盘交互。"""
    pygame.init()
    try:
        maze_w = maze.cols * cell_px + 2
        maze_h = maze.rows * cell_px + 2
        win_w = max(maze_w, MIN_WINDOW_WIDTH)
        win_h = maze_h + HUD_HEIGHT
        offset_x = (win_w - maze_w) // 2 + 1
        offset_y = 1

        screen = pygame.display.set_mode((win_w, win_h))
        pygame.display.set_caption(title)
        clock = pygame.time.Clock()
        try:
            font = pygame.font.SysFont("consolas,monospace", 15)
        except Exception:
            font = pygame.font.Font(None, 18)

        state = ReplayState(result, animate=animate)
        cur_maze = maze
        cur_result = result
        cur_status = status_text

        running = True
        while running:
            dt = clock.tick(fps) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key == pygame.K_r and on_regenerate is not None:
                        cur_maze, cur_result, cur_status = on_regenerate()
                        state.reset(cur_result, animate=animate)
                    elif event.key == pygame.K_g and on_switch_generator is not None:
                        cur_maze, cur_result, cur_status = on_switch_generator()
                        state.reset(cur_result, animate=animate)
                    elif event.key == pygame.K_SPACE and on_switch_solver is not None:
                        cur_result, cur_status = on_switch_solver(cur_maze)
                        state.reset(cur_result, animate=animate)
                    elif event.key == pygame.K_UP:
                        state.speed_up()
                    elif event.key == pygame.K_DOWN:
                        state.speed_down()
                    elif event.key == pygame.K_p:
                        state.toggle_pause()
                    elif event.key == pygame.K_s:
                        if state.is_finished:
                            state.reset(cur_result, animate=True)
                        else:
                            state.finish_immediately()

            state.advance(dt)

            screen.fill(HUD_BG_COLOR)
            draw_maze(
                screen,
                cur_maze,
                cur_result,
                cell_px=cell_px,
                offset_x=offset_x,
                offset_y=offset_y,
                visited_count=state.visited_idx,
                path_count=state.path_idx,
            )

            expanded = cur_result.expanded if cur_result is not None else 0
            path_len = len(cur_result.path) if cur_result is not None else 0
            if cur_result is None:
                play_state = "Static"
            elif state.is_finished:
                play_state = "Done"
            elif state.paused:
                play_state = "Paused"
            else:
                play_state = "Running"

            prefix = f"{cur_status} | " if cur_status else ""
            line1 = (
                f"{prefix}Expanded: {expanded} | Path: {path_len} | "
                f"Speed: {state.speed}/s | {play_state}"
            )
            line2 = (
                "[R] Regen  [G] Gen  [Space] Solver  "
                "[Up/Down] Speed  [P] Pause  [S] Skip/Replay  [Q/Esc] Quit"
            )
            hud_rect = pygame.Rect(0, maze_h, win_w, HUD_HEIGHT)
            draw_hud(screen, hud_rect, line1, line2, font)
            pygame.display.flip()
    finally:
        pygame.quit()
