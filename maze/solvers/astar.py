"""A*（A-Star）启发式寻路求解器（使用手写 MinHeap）。

核心公式：f(n) = g(n) + h(n)
- g(n)：从起点走到当前格 n 的实际累计代价；
- h(n)：曼哈顿距离 |r - end_r| + |c - end_c|，估测从 n 到终点的最小剩余代价。
因为迷宫每格最小通行代价 >= 1，曼哈顿距离满足可采纳性与一致性，因此保证求得最优路径，
同时借助启发函数优先朝终点方向搜索，扩展节点数（expanded）远小于 BFS 和 Dijkstra。
"""
from __future__ import annotations

from maze.ds.min_heap import MinHeap
from maze.model import Maze, SolveResult


def manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    """计算两格之间的曼哈顿距离（四方向无障碍下界）。"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


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
    """使用手写 MinHeap 与曼哈顿启发函数实现 A* 寻路。最坏时间 O((V + E) log V)，空间 O(V)。"""
    start = maze.start if start is None else start
    end = maze.end if end is None else end

    g_score: dict[tuple[int, int], int] = {start: 0}
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    closed: set[tuple[int, int]] = set()
    visited_order: list[tuple[int, int]] = []

    h0 = manhattan(start, end)
    heap = MinHeap()
    # 堆元素：(f = g + h, h, 行, 列)；f 相同时优先扩展 h 更小（更靠近终点）的节点
    heap.push((h0, h0, start[0], start[1]))
    expanded = 0
    found = False

    while not heap.is_empty():
        _, _, r, c = heap.pop()
        cur = (r, c)
        if cur in closed:
            continue
        closed.add(cur)
        visited_order.append(cur)
        expanded += 1

        if cur == end:
            found = True
            break

        g = g_score[cur]
        for nb in maze.neighbors(r, c):
            if nb in closed:
                continue
            ng = g + maze.cell_cost(*nb)
            if ng < g_score.get(nb, float("inf")):
                g_score[nb] = ng
                parent[nb] = cur
                nh = manhattan(nb, end)
                heap.push((ng + nh, nh, nb[0], nb[1]))

    path = _reconstruct_path(parent, end) if found else []
    return SolveResult(
        path=path,
        visited_order=visited_order,
        found=found,
        expanded=expanded,
        cost=g_score[end] if found else 0,
    )
