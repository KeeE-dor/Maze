"""BFS 广度优先求解（B 同学 · 第 4 周）—— 队列版 + 按层递归版。

BFS 按"离起点的距离"一层层向外扩散，因此第一次摸到终点时，走过的层数
就是最短距离 —— path 一定是最短路。
答辩题"为什么"：反证——若存在更短路径，它上面必有一格比当前格更早入队，
那一次扩展就先到终点了。

solve_queue：标准版，必须用 maze/ds/queue.py 的手写队列；
    出队一格 -> 标记/记录 -> 未访问邻居全部入队并记 parent。
    终点出队时停（不是入队时停也行，但出队时停的判据更简单）。

solve_recursive：课程要求的"递归 BFS"。BFS 本质基于队列，这里的做法是
【按层递归】—— 每次调用处理完当前一整层，把收集到的下一层作为列表传给自己：

    def _layer(frontier, ...):
        next_frontier = []
        for cur in frontier:
            ...处理 cur，收集它未访问的邻居...
        if next_frontier:
            _layer(next_frontier, ...)

递归深度 = 最短路的层数（迷宫路径长时会深，同样吃 Python 递归上限），
这是它和队列版的本质差别 —— 队列版把"层"存在堆外的队列里，递归版存在调用栈里。
答辩务必能讲清这一点。
"""
from __future__ import annotations

from maze.model import Maze, SolveResult


def solve_queue(maze: Maze, start: tuple[int, int] | None = None,
                end: tuple[int, int] | None = None) -> SolveResult:
    """TODO 第 4 周：队列版 BFS（手写 Queue + parent 回溯）。"""
    raise NotImplementedError("TODO 第 4 周：队列版 BFS")


def solve_recursive(maze: Maze, start: tuple[int, int] | None = None,
                    end: tuple[int, int] | None = None) -> SolveResult:
    """TODO 第 4 周：按层递归版 BFS（实现思路见模块 docstring）。"""
    raise NotImplementedError("TODO 第 4 周：按层递归 BFS")
