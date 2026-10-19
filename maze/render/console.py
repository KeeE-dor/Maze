"""终端字符画渲染 —— 已实现，作为第 1 周"能跑"的示范，也贯穿全程做快速验证。

先终端、后 Pygame 的原因（见 项目计划.md 二-3）：
把"算法对不对"和"界面好不好看"分开验证，出问题时能立刻定位是算法错还是渲染错。
第 3 周里程碑 M1 靠它验收，第 7 周答辩也可以拿它做兜底演示。

画法（纯 ASCII，任何终端都不会乱码）：
    +---+---+
    | S   E |     上边界/横墙：+ ---
    +   +   +     竖墙：|
    +---+---+     S 起点 / E 终点 / * 路径
只看每格的 W 墙和 S 墙即可画出整个迷宫（内部墙两侧共享同一位），
最右列与最下行永远是外边界。
"""
from __future__ import annotations

from maze.model import Maze, S, W


def render(maze: Maze, path: list[tuple[int, int]] | None = None) -> str:
    """把迷宫渲染成多行字符串返回（不打印，方便测试和拼接）。

    path 非空时高亮：S=起点 E=终点 *=路径上的格子。
    """
    marks = {maze.start: "S", maze.end: "E"}
    for cell in path or []:
        marks.setdefault(cell, "*")

    lines = ["+" + "---+" * maze.cols]  # 上边界
    for r in range(maze.rows):
        row = ""
        sep = "+"
        for c in range(maze.cols):
            west = "|" if c == 0 or maze.has_wall(r, c, W) else " "
            row += west + f" {marks.get((r, c), ' ')} "
            sep += "---+" if maze.has_wall(r, c, S) else "   +"
        row += "|"  # 最右列的外边界
        lines.append(row)
        if r == maze.rows - 1:
            lines.append("+" + "---+" * maze.cols)  # 下边界
        else:
            lines.append(sep)
    return "\n".join(lines)


def print_maze(maze: Maze, path: list[tuple[int, int]] | None = None) -> None:
    """渲染并直接 print（命令行调试用）。"""
    print(render(maze, path))
