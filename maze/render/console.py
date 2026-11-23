"""终端 ASCII 字符画渲染（S 起点，E 终点，* 路径）。"""
from __future__ import annotations

from maze.model import Maze, S, W


def render(maze: Maze, path: list[tuple[int, int]] | None = None) -> str:
    """将迷宫渲染为多行 ASCII 字符串，传入 path 时标记路径。"""
    marks = {maze.start: "S", maze.end: "E"}
    for cell in path or []:
        marks.setdefault(cell, "*")

    lines = ["+" + "---+" * maze.cols]
    for r in range(maze.rows):
        row = ""
        sep = "+"
        for c in range(maze.cols):
            west = "|" if c == 0 or maze.has_wall(r, c, W) else " "
            row += west + f" {marks.get((r, c), ' ')} "
            sep += "---+" if maze.has_wall(r, c, S) else "   +"
        row += "|"
        lines.append(row)
        if r == maze.rows - 1:
            lines.append("+" + "---+" * maze.cols)
        else:
            lines.append(sep)
    return "\n".join(lines)


def print_maze(maze: Maze, path: list[tuple[int, int]] | None = None) -> None:
    """将迷宫渲染结果直接打印到终端。"""
    print(render(maze, path))
