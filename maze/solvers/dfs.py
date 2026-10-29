"""DFS 深度优先求解（B 同学 · 第 3 周）—— 递归版 + 非递归（手写栈）版。

两个版本共同要求：
    * 返回 SolveResult；visited_order 记录【首次访问】顺序供动画回放；
    * 找到终点立刻收手（迷宫求解不需要遍历全部）；
    * 路径 path 用 parent 字典回溯：parent[下一格] = 当前格，
      到达终点后从终点沿 parent 走回起点再反转。

递归版 solve_recursive 的注意点：
    * Python 默认递归上限 1000 —— 大迷宫（如 50×50 的长蛇形路径）会 RecursionError；
      在 main.py 里 sys.setrecursionlimit(10**6) 兜底；
    * 答辩要能解释：这是递归版固有局限（调用栈深度 = 迷宫深度），不是 bug。

非递归版 solve_iterative 的注意点：
    * 必须用 maze/ds/stack.py 的手写 Stack（得分点），不许拿 list 凑合；
    * 【入栈的同时】就标记 visited，否则同一格会被压栈多次导致爆栈/超时；
    * 弹栈 -> 若是终点则收手 -> 否则把未访问的可达邻居逐个入栈。

expanded 的统一口径（四种求解器必须一致，对比实验用）：
    一个格子被"处理"一次（迭代版弹栈一次 / 递归版进入 _walk 一次）计 1。
完美迷宫是树，两点间简单路径唯一，所以两版求得的 path 必然完全一致
（真正有差异的是 expanded 与 visited_order，报告对比用）。
"""
from __future__ import annotations

from maze.ds.stack import Stack
from maze.model import Maze, SolveResult


def solve_recursive(maze: Maze, start: tuple[int, int] | None = None,
                    end: tuple[int, int] | None = None) -> SolveResult:
    """递归 DFS。时间复杂度 O(V+E)=O(cells)，空间 O(cells)（visited + 递归栈）。"""
    start = maze.start if start is None else start
    end = maze.end if end is None else end

    visited: set[tuple[int, int]] = set()
    visited_order: list[tuple[int, int]] = []
    on_path: list[tuple[int, int]] = []  # 当前递归链；找到终点时它恰好就是解
    expanded = 0

    def _walk(cur: tuple[int, int]) -> bool:
        """从 cur 出发找 end；True 表示已找到，逐层短路返回。"""
        nonlocal expanded
        visited.add(cur)
        visited_order.append(cur)
        expanded += 1
        on_path.append(cur)
        if cur == end:
            return True
        for nb in maze.neighbors(*cur):
            if nb not in visited and _walk(nb):
                return True  # 已找到：不再探索其余邻居，层层短路
        on_path.pop()  # 从 cur 出发找不到终点：回溯（撤销 cur 在路径上）
        return False

    found = _walk(start)
    return SolveResult(
        path=list(on_path) if found else [],
        visited_order=visited_order,
        found=found,
        expanded=expanded,
    )


def solve_iterative(maze: Maze, start: tuple[int, int] | None = None,
                    end: tuple[int, int] | None = None) -> SolveResult:
    """非递归 DFS（手写 Stack）。时间复杂度 O(V+E)=O(cells)，空间 O(cells)。"""
    start = maze.start if start is None else start
    end = maze.end if end is None else end

    visited: set[tuple[int, int]] = {start}
    visited_order: list[tuple[int, int]] = [start]
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    stack = Stack()  # 得分点：手写栈
    stack.push(start)
    expanded = 0
    found = False

    while not stack.is_empty():
        cur = stack.pop()
        expanded += 1
        if cur == end:
            found = True
            break  # 找到终点立刻收手
        for nb in maze.neighbors(*cur):
            if nb not in visited:
                # 必须在入栈时就标 visited：弹栈才标会让同一格被反复压栈
                visited.add(nb)
                visited_order.append(nb)
                parent[nb] = cur
                stack.push(nb)

    path: list[tuple[int, int]] = []
    if found:
        node: tuple[int, int] | None = end
        while node is not None:
            path.append(node)
            node = parent[node]
        path.reverse()
    return SolveResult(
        path=path,
        visited_order=visited_order,
        found=found,
        expanded=expanded,
    )
