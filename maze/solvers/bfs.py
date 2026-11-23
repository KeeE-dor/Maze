"""BFS 迷宫求解：提供基于手写 Queue 的队列版与按层递归版，保证求得最短路径。"""
from __future__ import annotations

from maze.ds.queue import Queue
from maze.model import Maze, SolveResult


def _reconstruct_path(
    parent: dict[tuple[int, int], tuple[int, int] | None],
    end: tuple[int, int],
) -> list[tuple[int, int]]:
    path: list[tuple[int, int]] = []
    node: tuple[int, int] | None = end
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path


def solve_queue(
    maze: Maze,
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
) -> SolveResult:
    """队列版 BFS（手写循环队列）。O(V + E) = O(cells)，空间 O(cells)。"""
    start = maze.start if start is None else start
    end = maze.end if end is None else end

    visited: set[tuple[int, int]] = {start}
    visited_order: list[tuple[int, int]] = [start]
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    queue = Queue()
    queue.enqueue(start)
    expanded = 0
    found = False

    while not queue.is_empty():
        cur = queue.dequeue()
        expanded += 1
        if cur == end:
            found = True
            break
        for nb in maze.neighbors(*cur):
            if nb not in visited:
                visited.add(nb)
                visited_order.append(nb)
                parent[nb] = cur
                queue.enqueue(nb)

    path = _reconstruct_path(parent, end) if found else []
    return SolveResult(
        path=path,
        visited_order=visited_order,
        found=found,
        expanded=expanded,
    )


def solve_recursive(
    maze: Maze,
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
) -> SolveResult:
    """按层递归版 BFS：逐层收集 next_frontier 递归，调用栈深度等于最短路层数。O(V + E)。"""
    start = maze.start if start is None else start
    end = maze.end if end is None else end

    visited: set[tuple[int, int]] = {start}
    visited_order: list[tuple[int, int]] = [start]
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    expanded = 0
    found = False

    def _layer(frontier: list[tuple[int, int]]) -> None:
        nonlocal expanded, found
        next_frontier: list[tuple[int, int]] = []
        for cur in frontier:
            expanded += 1
            if cur == end:
                found = True
                return
            for nb in maze.neighbors(*cur):
                if nb not in visited:
                    visited.add(nb)
                    visited_order.append(nb)
                    parent[nb] = cur
                    next_frontier.append(nb)
        if next_frontier:
            _layer(next_frontier)

    _layer([start])
    path = _reconstruct_path(parent, end) if found else []
    return SolveResult(
        path=path,
        visited_order=visited_order,
        found=found,
        expanded=expanded,
    )
