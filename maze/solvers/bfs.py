"""BFS（广度优先搜索）迷宫求解器：提供手写队列版与按层递归版。

核心特点：
BFS 按离起点的步数“一圈一圈”向外扩散，所以第一次到达终点时走过的步数必然是最少的（保证最短路）。
"""
from __future__ import annotations

from maze.ds.queue import Queue
from maze.model import Maze, SolveResult


def _reconstruct_path(
    parent: dict[tuple[int, int], tuple[int, int] | None],
    end: tuple[int, int],
) -> list[tuple[int, int]]:
    """根据 parent 字典记录的“前驱节点”，从终点一路倒推回起点再反转，得到正向路径。"""
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
    """队列版 BFS（使用手写循环队列 Queue）。O(V + E) = O(cells)，空间 O(cells)。"""
    start = maze.start if start is None else start
    end = maze.end if end is None else end

    # visited 记录已经入过队的格子（防止走回头路或重复入队）
    visited: set[tuple[int, int]] = {start}
    # visited_order 记录首次访问顺序，供 Pygame 动画逐步回放
    visited_order: list[tuple[int, int]] = [start]
    # parent 记录每个格子是从哪个格子走过来的，用于最后回溯路径
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}

    queue = Queue()
    queue.enqueue(start)
    expanded = 0  # 统计出队（实际扩展）的节点次数
    found = False

    while not queue.is_empty():
        cur = queue.dequeue()
        expanded += 1
        # 只要出队的是终点，说明已经找到最短路径，立即停止搜索
        if cur == end:
            found = True
            break
        # 把当前格所有“没墙且未访问”的邻居依次入队
        for nb in maze.neighbors(*cur):
            if nb not in visited:
                # 必须在入队时就标记 visited，否则同一格可能被多个邻居重复入队
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
        cost=maze.path_cost(path),
    )


def solve_recursive(
    maze: Maze,
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
) -> SolveResult:
    """按层递归版 BFS：每次递归处理完当前一整层，把收集到的下一层传给自己。

    与队列版的差异：队列版把待扩展节点存在显式 Queue 里，递归深度为 1；
    按层递归版把每一层的列表留在系统调用栈里，递归深度等于最短路径的步数。O(V + E)。
    """
    start = maze.start if start is None else start
    end = maze.end if end is None else end

    visited: set[tuple[int, int]] = {start}
    visited_order: list[tuple[int, int]] = [start]
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    expanded = 0
    found = False

    def _layer(frontier: list[tuple[int, int]]) -> None:
        """处理当前层 frontier 中的所有节点，并收集下一层 next_frontier。"""
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
        # 只有下一层还有新节点时，才继续递归进入下一层
        if next_frontier:
            _layer(next_frontier)

    _layer([start])
    path = _reconstruct_path(parent, end) if found else []
    return SolveResult(
        path=path,
        visited_order=visited_order,
        found=found,
        expanded=expanded,
        cost=maze.path_cost(path),
    )
