"""迷宫生成与求解演示入口。

常用运行方式：
    python main.py                              # 默认启动 Qt 图形界面（含生成动画 + 手动走 + 多算法对比）
    python main.py --console --seed 42          # 终端模式：6 种求解器对比 + 路径高亮
    python main.py --console --gen division --loop-ratio 0.1 --mud-ratio 0.2 --seed 42

注意：OPEN、carve_demo_maze、demo_path 供 tests/test_solvers.py 单元测试使用，请勿删除。
"""
from __future__ import annotations

import argparse
import random
import sys
from typing import Callable

from maze import Maze, SolveResult
from maze.generators import kruskal, prim, recursive_backtracker, recursive_division
from maze.render import console
from maze.solvers import astar, bfs, dfs, dijkstra

# Python 默认递归深度上限仅 1000，大迷宫下递归版 DFS/BFS 会触发 RecursionError，这里预先放宽
sys.setrecursionlimit(10**6)

# 硬编码 6×6 蛇形单走廊迷宫的打通边列表（仅供单元测试确定性校验）
OPEN = [
    ((0, 0), (0, 1)), ((0, 1), (0, 2)), ((0, 2), (0, 3)), ((0, 3), (0, 4)), ((0, 4), (0, 5)),
    ((0, 5), (1, 5)), ((1, 5), (2, 5)),
    ((2, 5), (2, 4)), ((2, 4), (2, 3)), ((2, 3), (2, 2)), ((2, 2), (2, 1)), ((2, 1), (2, 0)),
    ((2, 0), (3, 0)), ((3, 0), (4, 0)),
    ((4, 0), (4, 1)), ((4, 1), (4, 2)), ((4, 2), (4, 3)), ((4, 3), (4, 4)), ((4, 4), (4, 5)),
    ((4, 5), (5, 5)), ((5, 5), (5, 4)), ((5, 4), (5, 3)), ((5, 3), (5, 2)), ((5, 2), (5, 1)),
    ((5, 1), (5, 0)),
]

# 支持切换的生成算法注册表：(命令行标识, 界面显示名, 生成函数)
GENERATORS: list[tuple[str, str, Callable[..., Maze]]] = [
    ("kruskal", "Kruskal（最小生成树）", kruskal.generate),
    ("prim", "Prim（局部生长）", prim.generate),
    ("backtracker", "递归回溯（DFS 生成）", recursive_backtracker.generate),
    ("division", "递归分割法（房间筑墙）", recursive_division.generate),
]

# 支持切换的求解算法注册表（用于终端模式）
SOLVERS: list[tuple[str, str, Callable[[Maze], SolveResult]]] = [
    ("dfs_iterative", "DFS-Iter", dfs.solve_iterative),
    ("dfs_recursive", "DFS-Rec", dfs.solve_recursive),
    ("bfs_queue", "BFS-Queue", bfs.solve_queue),
    ("bfs_recursive", "BFS-Rec", bfs.solve_recursive),
    ("dijkstra", "Dijkstra", dijkstra.solve),
    ("astar", "A*", astar.solve),
]

# Qt 同屏对比模式专用：左右两侧均可自由挑选 BFS / DFS / Dijkstra / A* 任意版本进行同屏对比
BFS_SOLVERS: list[tuple[str, str, Callable[[Maze], SolveResult]]] = [
    ("bfs_queue", "BFS 队列版", bfs.solve_queue),
    ("bfs_recursive", "BFS 按层递归版", bfs.solve_recursive),
    ("astar", "A*（曼哈顿启发）", astar.solve),
    ("dijkstra", "Dijkstra（最小堆）", dijkstra.solve),
    ("dfs_recursive", "DFS 递归版（含回溯动画）", dfs.solve_recursive),
    ("dfs_iterative", "DFS 非递归版", dfs.solve_iterative),
]

DFS_SOLVERS: list[tuple[str, str, Callable[[Maze], SolveResult]]] = [
    ("dfs_recursive", "DFS 递归版（含回溯动画）", dfs.solve_recursive),
    ("dfs_iterative", "DFS 非递归版", dfs.solve_iterative),
    ("astar", "A*（曼哈顿启发）", astar.solve),
    ("dijkstra", "Dijkstra（最小堆）", dijkstra.solve),
    ("bfs_queue", "BFS 队列版", bfs.solve_queue),
    ("bfs_recursive", "BFS 按层递归版", bfs.solve_recursive),
]


def carve_demo_maze() -> Maze:
    """按 OPEN 拆墙，构造一条从 (0,0) 到 (5,0) 的蛇形通道（测试用）。"""
    m = Maze(6, 6)
    for a, b in OPEN:
        m.remove_wall_between(a, b)
    return m


def demo_path(maze: Maze) -> list[tuple[int, int]]:
    """返回蛇形迷宫的唯一完整路径（测试用）。"""
    return [maze.start] + [b for _, b in OPEN]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="迷宫生成与求解系统演示")
    parser.add_argument("--rows", type=int, default=15, help="迷宫行数（默认 15）")
    parser.add_argument("--cols", type=int, default=15, help="迷宫列数（默认 15）")
    parser.add_argument(
        "--gen",
        choices=[key for key, _, _ in GENERATORS],
        default="kruskal",
        help="迷宫生成算法（默认 kruskal）",
    )
    parser.add_argument(
        "--solver",
        choices=[key for key, _, _ in SOLVERS],
        default="astar",
        help="迷宫求解算法（默认 astar，用于终端模式）",
    )
    parser.add_argument(
        "--loop-ratio",
        type=float,
        default=0.0,
        help="额外拆环比例 0.0~0.4（默认 0.0，大于 0 时生成含环多路径迷宫）",
    )
    parser.add_argument(
        "--mud-ratio",
        type=float,
        default=0.0,
        help="高代价泥地比例 0.0~0.5（默认 0.0，泥地通行代价为 5）",
    )
    parser.add_argument("--seed", type=int, default=None, help="随机种子（可选）")
    parser.add_argument("--console", action="store_true", help="终端模式（不启动图形界面）")
    return parser.parse_args(argv)


def _run_console(
    maze: Maze,
    gen_label: str,
    selected_solver_key: str,
    *,
    is_perfect: bool = True,
) -> None:
    """终端演示模式：打印迷宫、对比六种求解器指标并高亮输出选定路径。"""
    print(f"== 终端演示：{gen_label} 生成 {maze.rows}×{maze.cols} ==")
    console.print_maze(maze)

    results: dict[str, SolveResult] = {}
    print("\n== 六种求解器对比（同一迷宫）==")
    print(f"{'算法':<12} | {'found':<5} | {'路径长':<6} | {'总代价':<6} | {'expanded':<8}")
    print("-" * 51)
    for key, label, solve_fn in SOLVERS:
        res = solve_fn(maze)
        results[key] = res
        print(
            f"{label:<12} | {str(res.found):<5} | {len(res.path):<6} | "
            f"{res.cost:<6} | {res.expanded:<8}"
        )

    if is_perfect:
        paths = [res.path for res in results.values()]
        assert all(p == paths[0] for p in paths), "完美迷宫上所有求解器的 path 必须完全一致"
    else:
        assert len(results["bfs_queue"].path) <= len(results["dfs_iterative"].path)
        assert results["dijkstra"].cost == results["astar"].cost <= results["bfs_queue"].cost

    chosen = results[selected_solver_key]
    chosen_label = dict((k, lbl) for k, lbl, _ in SOLVERS)[selected_solver_key]
    print(
        f"\n== 路径高亮（{chosen_label}, expanded={chosen.expanded}, "
        f"路径长={len(chosen.path)}, 总代价={chosen.cost}）=="
    )
    console.print_maze(maze, chosen.path)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    gen_idx = [k for k, _, _ in GENERATORS].index(args.gen)

    if args.console:
        rng = random.Random(args.seed) if args.seed is not None else random.Random()
        _, g_label, gen_fn = GENERATORS[gen_idx]
        maze = gen_fn(args.rows, args.cols, rng=rng)
        if args.loop_ratio > 0:
            maze.add_loops(args.loop_ratio, rng=rng)
        if args.mud_ratio > 0:
            maze.apply_weighted_terrain(args.mud_ratio, rng=rng)
        _run_console(
            maze,
            g_label,
            args.solver,
            is_perfect=(args.loop_ratio <= 0 and not maze.has_weighted_terrain()),
        )
        return

    # 默认启动 Qt（PySide6）图形界面：先弹配置窗询问尺寸、生成方式与含环/泥地配置，再进入交互主窗口
    from maze.render import qt_view

    qt_view.run_app(
        GENERATORS,
        BFS_SOLVERS,
        DFS_SOLVERS,
        initial_rows=args.rows,
        initial_cols=args.cols,
        initial_gen=args.gen,
        initial_loop_ratio=args.loop_ratio,
        initial_mud_ratio=args.mud_ratio,
    )


if __name__ == "__main__":
    main()
