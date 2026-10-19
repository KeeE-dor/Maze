"""Pygame 可视化（B 同学 · 第 4–5 周）。

架构：回放式动画 —— 求解器一次算完，把 SolveResult.visited_order 交给这里逐帧回放。
计算与渲染彻底解耦：算法代码里不许 import pygame，渲染代码里不许写算法逻辑。
好处：动画速度可调、可暂停，答辩演示可控；换算法不用动渲染，换渲染不用动算法。

建议实现顺序（每周一小步，先 30 行热身再填这里）：
    第 4 周·静态：pygame.init -> 窗口 -> 每格画底色矩形 -> 按位掩码画四面墙线
                  -> path 格子高亮 -> 主循环 event.get(QUIT) + flip
    第 5 周·动画：每帧从 visited_order 消费一个格子染色（用 Clock.tick 控速），
                  全部放完后再逐格描 path
    第 5 周·交互：R 重新生成 / 空格切换算法 / 上下方向键调速

最小知识清单：pygame.init / display.set_mode / screen.fill /
pygame.draw.rect / pygame.draw.line / event.get(QUIT, KEYDOWN) /
display.flip + Clock.tick(fps)。先照官方 quick start 写个"画方块的窗口"热身。
"""
from __future__ import annotations

import pygame

from maze.model import Maze, N, E, S, W, DELTA, SolveResult

WALL_COLOR = (40, 40, 40)
CELL_COLOR = (245, 245, 240)
PATH_COLOR = (255, 200, 60)
VISITED_COLOR = (180, 210, 255)
START_COLOR = (80, 200, 120)
END_COLOR = (230, 90, 90)


def run(maze: Maze, result: SolveResult | None = None, cell_px: int = 24, fps: int = 60) -> None:
    """打开窗口渲染迷宫；result 给了就回放动画。

    TODO 第 4 周：静态渲染（墙线 + path 高亮）。
    TODO 第 5 周：按 visited_order 回放动画 + 键盘交互。
    窗口尺寸 = cols * cell_px × rows * cell_px，别忘边缘留 1px 画外边框。
    """
    raise NotImplementedError("TODO 第 4–5 周：Pygame 渲染（见本文件上方的实现顺序）")
