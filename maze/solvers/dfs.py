"""DFS（深度优先搜索）迷宫求解器：提供递归版与基于手写 Stack 的非递归版。

核心特点：
沿着一条路一直往深处走，走不通（死胡同）再退回上一个分叉口换条路；找到终点就立刻停止。
"""
from __future__ import annotations

from maze.ds.stack import Stack
from maze.model import Maze, SolveResult


def solve_recursive(
    maze: Maze,
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
) -> SolveResult:
    """递归版 DFS。O(V + E) = O(cells)，空间 O(cells)。"""
    start = maze.start if start is None else start
    end = maze.end if end is None else end

    visited: set[tuple[int, int]] = set()
    visited_order: list[tuple[int, int]] = []
    on_path: list[tuple[int, int]] = []  # 记录当前正在探索的递归路径链
    trace: list[tuple[str, tuple[int, int]]] = []  # 记录探索与回溯事件流，供动画展示回溯过程
    expanded = 0

    def _walk(cur: tuple[int, int]) -> bool:
        """从 cur 出发深度探索；返回 True 表示已经找到终点，层层直接退出。"""
        nonlocal expanded
        visited.add(cur)
        visited_order.append(cur)
        trace.append(("visit", cur))
        expanded += 1
        on_path.append(cur)
        if cur == end:
            return True
        for nb in maze.neighbors(*cur):
            # 只要有一个邻居最终能走到终点，就不再试其它方向，直接逐层返回 True
            if nb not in visited and _walk(nb):
                return True
        # 所有邻居都走不通，说明 cur 在死胡同里，回溯时把它从当前路径移除并记录回溯事件
        on_path.pop()
        trace.append(("backtrack", cur))
        return False

    found = _walk(start)
    final_path = list(on_path) if found else []
    return SolveResult(
        path=final_path,
        visited_order=visited_order,
        found=found,
        expanded=expanded,
        trace=trace,
        cost=maze.path_cost(final_path),
    )


def solve_iterative(
    maze: Maze,
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
) -> SolveResult:
    """非递归版 DFS（使用手写栈 Stack 模拟系统调用栈）。O(V + E) = O(cells)，空间 O(cells)。"""
    start = maze.start if start is None else start
    end = maze.end if end is None else end

    visited: set[tuple[int, int]] = {start}
    visited_order: list[tuple[int, int]] = [start]
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    stack = Stack()
    stack.push(start)
    expanded = 0
    found = False

    while not stack.is_empty():
        cur = stack.pop()
        expanded += 1
        if cur == end:
            found = True
            break
        for nb in maze.neighbors(*cur):
            if nb not in visited:
                # 必须在入栈时就标记 visited，否则同一格子会被多个分支反复压栈
                visited.add(nb)
                visited_order.append(nb)
                parent[nb] = cur
                stack.push(nb)

    # 找到终点后，沿 parent 字典从终点倒推回起点，再反转为正向路径
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
        cost=maze.path_cost(path),
    )
