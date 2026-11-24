"""Dijkstra 最短路求解器（使用手写 MinHeap）。

适用场景：
当迷宫中存在“泥地”等高通行代价地形（或含环多路径）时，BFS 只能保证步数最少，
而 Dijkstra 会按累计代价从小到大扩展节点，严格保证找到总代价最小的路径。
"""
from __future__ import annotations

from maze.ds.min_heap import MinHeap
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


def solve(
    maze: Maze,
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
) -> SolveResult:
    """使用手写 MinHeap 实现 Dijkstra 算法求最小代价路径。时间 O((V + E) log V)，空间 O(V)。"""
    start = maze.start if start is None else start
    end = maze.end if end is None else end

    dist: dict[tuple[int, int], int] = {start: 0}
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    settled: set[tuple[int, int]] = set()
    visited_order: list[tuple[int, int]] = []

    heap = MinHeap()
    heap.push((0, start[0], start[1]))  # 堆元素格式：(累计代价 g, 行, 列)
    expanded = 0
    found = False

    while not heap.is_empty():
        d, r, c = heap.pop()
        cur = (r, c)
        # 惰性删除：同一节点可能因更优路径多次入堆，已确定最短路的直接跳过
        if cur in settled:
            continue
        settled.add(cur)
        visited_order.append(cur)
        expanded += 1

        if cur == end:
            found = True
            break

        for nb in maze.neighbors(r, c):
            if nb in settled:
                continue
            nd = d + maze.cell_cost(*nb)
            if nd < dist.get(nb, float("inf")):
                dist[nb] = nd
                parent[nb] = cur
                heap.push((nd, nb[0], nb[1]))

    path = _reconstruct_path(parent, end) if found else []
    return SolveResult(
        path=path,
        visited_order=visited_order,
        found=found,
        expanded=expanded,
        cost=dist[end] if found else 0,
    )
