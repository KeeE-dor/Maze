"""DFS 深度优先求解（B 同学 · 第 3 周）—— 递归版 + 非递归（手写栈）版。

两个版本共同要求：
    * 返回 SolveResult；visited_order 记录【首次访问】顺序供动画回放；
    * 找到终点立刻收手（迷宫求解不需要遍历全部）；
    * 路径 path 用 parent 字典回溯：parent[下一格] = 当前格，
      到达终点后从终点沿 parent 走回起点再反转。

递归版 solve_recursive 的注意点：
    * Python 默认递归上限 1000 —— 大迷宫（如 50×50 的长蛇形路径）会 RecursionError；
      在 main.py 里 sys.setrecursionlimit(10**6) 兜底；
    * 答辩要能解释：这是递归版固有局限（调用栈深度 = 迷回深度），不是 bug。

非递归版 solve_iterative 的注意点：
    * 必须用 maze/ds/stack.py 的手写 Stack（得分点），不许拿 list 凑合；
    * 【入栈的同时】就标记 visited，否则同一格会被压栈多次导致爆栈/超时；
    * 弹栈 -> 若是终点则收手 -> 否则把未访问的可达邻居逐个入栈。
"""
from __future__ import annotations

from maze.model import Maze, SolveResult


def solve_recursive(maze: Maze, start: tuple[int, int] | None = None,
                    end: tuple[int, int] | None = None) -> SolveResult:
    """TODO 第 3 周：递归 DFS。

    hint：写一个内部函数 _walk(cur) -> bool（True 表示已找到终点，逐层短路），
    visited_order 在进入 _walk 时 append；返回时把 expanded 累加好。
    """
    raise NotImplementedError("TODO 第 3 周：递归 DFS")


def solve_iterative(maze: Maze, start: tuple[int, int] | None = None,
                    end: tuple[int, int] | None = None) -> SolveResult:
    """TODO 第 3 周：非递归 DFS（手写 Stack）。"""
    raise NotImplementedError("TODO 第 3 周：非递归 DFS")
