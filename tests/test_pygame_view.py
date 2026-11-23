"""Pygame 渲染层与回放状态机单元测试。"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from main import carve_demo_maze
from maze.model import SolveResult
from maze.render import pygame_view
from maze.solvers import bfs


def test_replay_state_progression_and_controls():
    res = SolveResult(
        path=[(0, 0), (0, 1), (1, 1)],
        visited_order=[(0, 0), (0, 1), (1, 0), (1, 1)],
        found=True,
        expanded=4,
    )
    state = pygame_view.ReplayState(res, animate=True, speed_idx=0)  # 5 格/秒
    assert state.visited_idx == 0 and state.path_idx == 0
    assert not state.is_finished

    state.advance(0.6)
    assert state.visited_idx == 3 and state.path_idx == 0

    state.toggle_pause()
    state.advance(1.0)
    assert state.visited_idx == 3 and state.path_idx == 0

    state.toggle_pause()
    state.advance(0.4)
    assert state.visited_idx == 4 and state.path_idx == 1

    state.finish_immediately()
    assert state.is_finished
    assert state.visited_idx == 4 and state.path_idx == 3

    state.reset(res, animate=False)
    assert state.is_finished

    for _ in range(20):
        state.speed_up()
    assert state.speed == pygame_view.SPEED_LEVELS[-1]
    for _ in range(20):
        state.speed_down()
    assert state.speed == pygame_view.SPEED_LEVELS[0]


def test_draw_maze_and_hud_headless():
    maze = carve_demo_maze()
    result = bfs.solve_queue(maze)
    cell_px = 20
    surf = pygame.Surface((maze.cols * cell_px + 2, maze.rows * cell_px + 2 + pygame_view.HUD_HEIGHT))

    pygame.init()
    try:
        font = pygame.font.Font(None, 18)
        pygame_view.draw_maze(surf, maze, result, cell_px=cell_px, offset_x=1, offset_y=1)
        assert surf.get_at((1 + cell_px // 2, 1 + cell_px // 2))[:3] == pygame_view.START_COLOR
        ex = 1 + 5 * cell_px + cell_px // 2
        ey = 1 + 5 * cell_px + cell_px // 2
        assert surf.get_at((ex, ey))[:3] == pygame_view.END_COLOR

        hud_rect = pygame.Rect(0, maze.rows * cell_px + 2, surf.get_width(), pygame_view.HUD_HEIGHT)
        pygame_view.draw_hud(surf, hud_rect, "Gen: Kruskal | Expanded: 31", "[R] Regen", font)
        assert surf.get_at((2, hud_rect.y + 2))[:3] == pygame_view.HUD_BG_COLOR
    finally:
        pygame.quit()


def test_pygame_view_decoupled_from_algorithms():
    """确保渲染层不直接导入任何生成或求解算法模块。"""
    src = (Path(__file__).resolve().parent.parent / "maze" / "render" / "pygame_view.py").read_text(
        encoding="utf-8"
    )
    assert "maze.generators" not in src
    assert "maze.solvers" not in src
