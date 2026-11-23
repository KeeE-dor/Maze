"""迷宫生成与求解正确性验证脚本（完美迷宫检查、防穿墙检查、算法交叉验证）。

运行：python scripts/verify.py
"""
from __future__ import annotations

from pathlib import Path
import random
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from maze.ds.union_find import UnionFind
from maze.generators import kruskal, prim
from maze.model import E, Maze, N, OPPOSITE, S, SolveResult, W
from maze.solvers import bfs, dfs

sys.setrecursionlimit(10**6)

SOLVER_MAP = {
    "dfs_recursive": dfs.solve_recursive,
    "dfs_iterative": dfs.solve_iterative,
    "bfs_queue": bfs.solve_queue,
    "bfs_recursive": bfs.solve_recursive,
}


def verify_perfect_maze(maze: Maze) -> tuple[bool, str]:
    """检查迷宫外墙封闭、内部墙对称、拆墙数等于 N-1，且无环全连通。"""
    rows, cols = maze.rows, maze.cols
    for c in range(cols):
        if not maze.has_wall(0, c, N):
            return False, f"上边界 (0, {c}) 缺失外墙"
        if not maze.has_wall(rows - 1, c, S):
            return False, f"下边界 ({rows - 1}, {c}) 缺失外墙"
    for r in range(rows):
        if not maze.has_wall(r, 0, W):
            return False, f"左边界 ({r}, 0) 缺失外墙"
        if not maze.has_wall(r, cols - 1, E):
            return False, f"右边界 ({r}, {cols - 1}) 缺失外墙"

    uf = UnionFind(rows * cols)
    removed = 0
    for r in range(rows):
        for c in range(cols):
            if c + 1 < cols:
                has_e = maze.has_wall(r, c, E)
                has_w = maze.has_wall(r, c + 1, W)
                if has_e != has_w:
                    return False, f"({r},{c}) 与 ({r},{c + 1}) 墙位不对称"
                if not has_e:
                    removed += 1
                    if not uf.union(maze.cell_id(r, c), maze.cell_id(r, c + 1)):
                        return False, f"检测到环：({r},{c}) - ({r},{c + 1})"
            if r + 1 < rows:
                has_s = maze.has_wall(r, c, S)
                has_n = maze.has_wall(r + 1, c, N)
                if has_s != has_n:
                    return False, f"({r},{c}) 与 ({r + 1},{c}) 墙位不对称"
                if not has_s:
                    removed += 1
                    if not uf.union(maze.cell_id(r, c), maze.cell_id(r + 1, c)):
                        return False, f"检测到环：({r},{c}) - ({r + 1},{c})"

    expected_removed = rows * cols - 1
    if removed != expected_removed:
        return False, f"拆墙数为 {removed}，期望 {expected_removed}"
    if uf.count != 1:
        return False, f"连通分量数为 {uf.count}，期望 1"
    return True, f"完美迷宫校验通过 (拆墙 {removed}, 连通分量 {uf.count})"


def _direction_between(a: tuple[int, int], b: tuple[int, int]) -> int | None:
    dr = b[0] - a[0]
    dc = b[1] - a[1]
    if (dr, dc) == (-1, 0):
        return N
    if (dr, dc) == (0, 1):
        return E
    if (dr, dc) == (1, 0):
        return S
    if (dr, dc) == (0, -1):
        return W
    return None


def verify_solution_path(
    maze: Maze,
    result: SolveResult,
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
) -> tuple[bool, str]:
    """用 has_wall 双向校验路径合法性、首尾格及无重复节点。"""
    start = maze.start if start is None else start
    end = maze.end if end is None else end

    if not result.found:
        return False, "未找到路径 (found=False)"
    if not result.path:
        return False, "路径为空"
    if result.path[0] != start:
        return False, f"起点不匹配：{result.path[0]} != {start}"
    if result.path[-1] != end:
        return False, f"终点不匹配：{result.path[-1]} != {end}"
    if len(set(result.path)) != len(result.path):
        return False, "路径存在重复节点"

    for cell in result.path:
        if not maze.in_bounds(*cell):
            return False, f"路径坐标越界: {cell}"

    for a, b in zip(result.path, result.path[1:]):
        direction = _direction_between(a, b)
        if direction is None:
            return False, f"非相邻步跳转: {a} -> {b}"
        if maze.has_wall(a[0], a[1], direction):
            return False, f"穿墙错误: {a} 方向 {direction} 有墙"
        if maze.has_wall(b[0], b[1], OPPOSITE[direction]):
            return False, f"对侧穿墙错误: {b} 方向 {OPPOSITE[direction]} 有墙"

    return True, f"路径合法 (步数 {len(result.path)})"


def verify_cross_algorithms(maze: Maze, *, is_perfect: bool = True) -> tuple[bool, str]:
    """交叉验证四种求解器的路径合法性与 BFS <= DFS 长度约束。"""
    results: dict[str, SolveResult] = {}
    for name, solver in SOLVER_MAP.items():
        res = solver(maze)
        ok, msg = verify_solution_path(maze, res)
        if not ok:
            return False, f"{name} 失败: {msg}"
        results[name] = res

    bfs_q = results["bfs_queue"].path
    bfs_r = results["bfs_recursive"].path
    dfs_r = results["dfs_recursive"].path
    dfs_i = results["dfs_iterative"].path

    if len(bfs_q) != len(bfs_r):
        return False, f"两版 BFS 路径长度不一致: {len(bfs_q)} vs {len(bfs_r)}"
    if len(bfs_q) > len(dfs_r) or len(bfs_q) > len(dfs_i):
        return False, (
            f"BFS 路径长度 ({len(bfs_q)}) 超过了 DFS "
            f"(rec={len(dfs_r)}, iter={len(dfs_i)})"
        )
    if is_perfect and not (bfs_q == bfs_r == dfs_r == dfs_i):
        return False, "完美迷宫上四版求解器唯一路径不一致"

    return True, f"交叉校验通过 (BFS={len(bfs_q)}, DFS_rec={len(dfs_r)}, DFS_iter={len(dfs_i)})"


def _add_loops(maze: Maze, extra_openings: int, rng: random.Random) -> None:
    """在完美迷宫上随机多拆墙以构造含环图。"""
    candidates: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for r in range(maze.rows):
        for c in range(maze.cols):
            if c + 1 < maze.cols and maze.has_wall(r, c, E):
                candidates.append(((r, c), (r, c + 1)))
            if r + 1 < maze.rows and maze.has_wall(r, c, S):
                candidates.append(((r, c), (r + 1, c)))
    rng.shuffle(candidates)
    for a, b in candidates[:extra_openings]:
        maze.remove_wall_between(a, b)


def main() -> int:
    sizes = [(5, 5), (10, 10), (20, 20), (30, 30)]
    generators = [("kruskal", kruskal.generate), ("prim", prim.generate)]
    seeds = [101, 202, 303]

    total_checks = 0
    print("== 1. 完美迷宫与四求解器全量验证 ==")
    for gen_name, gen_fn in generators:
        for rows, cols in sizes:
            for seed in seeds:
                total_checks += 1
                maze = gen_fn(rows, cols, rng=random.Random(seed))
                ok, msg = verify_perfect_maze(maze)
                if not ok:
                    print(f"[FAIL] {gen_name} {rows}x{cols} seed={seed}: {msg}")
                    return 1
                ok, msg = verify_cross_algorithms(maze, is_perfect=True)
                if not ok:
                    print(f"[FAIL] {gen_name} {rows}x{cols} seed={seed}: {msg}")
                    return 1
        print(f"[PASS] {gen_name}: 4 种尺寸 × {len(seeds)} 种子（共 {len(sizes) * len(seeds)} 组）全部通过")

    print("\n== 2. 含环非完美迷宫验证（BFS 最短路 <= DFS） ==")
    strictly_shorter = 0
    loop_cases = 10
    for seed in range(1, loop_cases + 1):
        total_checks += 1
        rng = random.Random(seed + 1000)
        maze = kruskal.generate(15, 15, rng=rng)
        _add_loops(maze, extra_openings=35, rng=rng)
        ok, msg = verify_cross_algorithms(maze, is_perfect=False)
        if not ok:
            print(f"[FAIL] loop seed={seed}: {msg}")
            return 1
        bfs_len = len(bfs.solve_queue(maze).path)
        dfs_len = len(dfs.solve_iterative(maze).path)
        if bfs_len < dfs_len:
            strictly_shorter += 1

    if strictly_shorter == 0:
        print("[FAIL] 含环测试未观察到 BFS 严格短于 DFS 的案例")
        return 1

    print(
        f"[PASS] 含环迷宫 {loop_cases} 组全部满足 BFS <= DFS，"
        f"其中 {strictly_shorter}/{loop_cases} 组严格更短"
    )
    print(f"\n全部 {total_checks} 组验证全部通过！")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
