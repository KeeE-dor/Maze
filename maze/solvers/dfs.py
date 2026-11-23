"""DFS 迷宫求解：提供递归版与基于手写 Stack 的非递归版，到达终点立即停止。"""
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
    on_path: list[tuple[int, int]] = []
    expanded = 0

    def _walk(cur: tuple[int, int]) -> bool:
        nonlocal expanded
        visited.add(cur)
        visited_order.append(cur)
        expanded += 1
        on_path.append(cur)
        if cur == end:
            return True
        for nb in maze.neighbors(*cur):
            if nb not in visited and _walk(nb):
                return True
        on_path.pop()  # 死路回溯，移出当前路径
        return False

    found = _walk(start)
    return SolveResult(
        path=list(on_path) if found else [],
        visited_order=visited_order,
        found=found,
        expanded=expanded,
    )


def solve_iterative(
    maze: Maze,
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
) -> SolveResult:
    """非递归版 DFS（手写 Stack）。O(V + E) = O(cells)，空间 O(cells)。"""
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
                # 入栈即标 visited，防止同一节点被重复压栈
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
