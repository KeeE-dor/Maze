"""迷宫生成与求解演示入口。

常用运行方式：
    python main.py                              # Pygame 动画与键盘交互
    python main.py --static                     # Pygame 静态渲染
    python main.py --console --seed 42          # 终端对比与路径高亮
    python main.py --gen prim --solver bfs_queue --rows 20 --cols 30

注：OPEN、carve_demo_maze、demo_path 供 tests/test_solvers.py 使用，请勿删除。
"""
from __future__ import annotations

import argparse
import random
import sys
from typing import Callable

from maze import Maze, SolveResult
from maze.generators import kruskal, prim
from maze.render import console
from maze.solvers import bfs, dfs

# 放宽递归深度限制以支持大迷宫的递归版 DFS/BFS
sys.setrecursionlimit(10**6)

OPEN = [
    ((0, 0), (0, 1)), ((0, 1), (0, 2)), ((0, 2), (0, 3)), ((0, 3), (0, 4)), ((0, 4), (0, 5)),
    ((0, 5), (1, 5)), ((1, 5), (2, 5)),
    ((2, 5), (2, 4)), ((2, 4), (2, 3)), ((2, 3), (2, 2)), ((2, 2), (2, 1)), ((2, 1), (2, 0)),
    ((2, 0), (3, 0)), ((3, 0), (4, 0)),
    ((4, 0), (4, 1)), ((4, 1), (4, 2)), ((4, 2), (4, 3)), ((4, 3), (4, 4)), ((4, 4), (4, 5)),
    ((4, 5), (5, 5)), ((5, 5), (5, 4)), ((5, 4), (5, 3)), ((5, 3), (5, 2)), ((5, 2), (5, 1)),
    ((5, 1), (5, 0)),
]

GENERATORS: list[tuple[str, str, Callable[..., Maze]]] = [
    ("kruskal", "Kruskal", kruskal.generate),
    ("prim", "Prim", prim.generate),
]

SOLVERS: list[tuple[str, str, Callable[[Maze], SolveResult]]] = [
    ("dfs_iterative", "DFS-Iter", dfs.solve_iterative),
    ("dfs_recursive", "DFS-Rec", dfs.solve_recursive),
    ("bfs_queue", "BFS-Queue", bfs.solve_queue),
    ("bfs_recursive", "BFS-Rec", bfs.solve_recursive),
]


def carve_demo_maze() -> Maze:
    """构造从 (0,0) 到 (5,0) 的单走廊蛇形迷宫（供单元测试使用）。"""
    m = Maze(6, 6)
    for a, b in OPEN:
        m.remove_wall_between(a, b)
    return m


def demo_path(maze: Maze) -> list[tuple[int, int]]:
    """返回蛇形迷宫从起点出发的完整路径（供单元测试使用）。"""
    return [maze.start] + [b for _, b in OPEN]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="迷宫生成与求解系统演示")
    parser.add_argument("--rows", type=int, default=15, help="迷宫行数（默认 15）")
    parser.add_argument("--cols", type=int, default=25, help="迷宫列数（默认 25）")
    parser.add_argument(
        "--gen",
        choices=[key for key, _, _ in GENERATORS],
        default="kruskal",
        help="迷宫生成算法（默认 kruskal）",
    )
    parser.add_argument(
        "--solver",
        choices=[key for key, _, _ in SOLVERS],
        default="bfs_queue",
        help="迷宫求解算法（默认 bfs_queue）",
    )
    parser.add_argument("--seed", type=int, default=None, help="随机种子（可选）")
    parser.add_argument("--console", action="store_true", help="终端模式（不启动 Pygame）")
    parser.add_argument("--static", action="store_true", help="Pygame 静态渲染模式")
    parser.add_argument("--cell-px", type=int, default=28, help="单元格像素大小（默认 28）")
    parser.add_argument("--fps", type=int, default=60, help="刷新帧率（默认 60）")
    return parser.parse_args(argv)


def _run_console(
    maze: Maze,
    gen_label: str,
    selected_solver_key: str,
) -> None:
    print(f"== 终端演示：{gen_label} 生成 {maze.rows}×{maze.cols} ==")
    console.print_maze(maze)

    results: dict[str, SolveResult] = {}
    print("\n== 四种求解器对比（同一迷宫）==")
    print(f"{'算法':<12} | {'found':<5} | {'路径长':<6} | {'expanded':<8}")
    print("-" * 42)
    for key, label, solve_fn in SOLVERS:
        res = solve_fn(maze)
        results[key] = res
        print(f"{label:<12} | {str(res.found):<5} | {len(res.path):<6} | {res.expanded:<8}")

    paths = [res.path for res in results.values()]
    assert all(p == paths[0] for p in paths), "完美迷宫上四种求解器的 path 必须完全一致"

    chosen = results[selected_solver_key]
    chosen_label = dict((k, lbl) for k, lbl, _ in SOLVERS)[selected_solver_key]
    print(f"\n== 路径高亮（{chosen_label}, expanded={chosen.expanded}, 路径长={len(chosen.path)}）==")
    console.print_maze(maze, chosen.path)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    gen_idx = [k for k, _, _ in GENERATORS].index(args.gen)
    solver_idx = [k for k, _, _ in SOLVERS].index(args.solver)
    rng = random.Random(args.seed) if args.seed is not None else random.Random()

    def build_status() -> str:
        _, g_label, _ = GENERATORS[gen_idx]
        _, s_label, _ = SOLVERS[solver_idx]
        return f"Gen: {g_label} | Solver: {s_label}"

    def make_maze() -> Maze:
        _, _, gen_fn = GENERATORS[gen_idx]
        return gen_fn(args.rows, args.cols, rng=rng)

    def run_solver(m: Maze) -> SolveResult:
        _, _, solve_fn = SOLVERS[solver_idx]
        return solve_fn(m)

    maze = make_maze()
    if args.console:
        _run_console(maze, GENERATORS[gen_idx][1], args.solver)
        return

    try:
        from maze.render import pygame_view
    except ImportError as exc:
        print(f"Pygame 加载失败 ({exc})，自动降级为终端模式。")
        _run_console(maze, GENERATORS[gen_idx][1], args.solver)
        return

    result = run_solver(maze)

    def on_regenerate() -> tuple[Maze, SolveResult, str]:
        m = make_maze()
        return m, run_solver(m), build_status()

    def on_switch_generator() -> tuple[Maze, SolveResult, str]:
        nonlocal gen_idx
        gen_idx = (gen_idx + 1) % len(GENERATORS)
        m = make_maze()
        return m, run_solver(m), build_status()

    def on_switch_solver(m: Maze) -> tuple[SolveResult, str]:
        nonlocal solver_idx
        solver_idx = (solver_idx + 1) % len(SOLVERS)
        return run_solver(m), build_status()

    pygame_view.run(
        maze,
        result,
        cell_px=args.cell_px,
        fps=args.fps,
        animate=not args.static,
        status_text=build_status(),
        on_regenerate=on_regenerate,
        on_switch_solver=on_switch_solver,
        on_switch_generator=on_switch_generator,
    )


if __name__ == "__main__":
    main()
