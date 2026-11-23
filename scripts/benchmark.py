"""迷宫生成与求解性能基准测试脚本，结果导出到 CSV 并打印汇总表。

运行：python scripts/benchmark.py
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from pathlib import Path
import random
import sys
import time

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from maze.generators import kruskal, prim
from maze.model import Maze
from maze.solvers import bfs, dfs

sys.setrecursionlimit(10**6)

GENERATORS = [
    ("kruskal", kruskal.generate),
    ("prim", prim.generate),
]

SOLVERS = [
    ("dfs_recursive", dfs.solve_recursive),
    ("dfs_iterative", dfs.solve_iterative),
    ("bfs_queue", bfs.solve_queue),
    ("bfs_recursive", bfs.solve_recursive),
]


def count_dead_ends(maze: Maze) -> int:
    """统计只有 1 个可达邻居的死胡同数量。"""
    dead_ends = 0
    for r in range(maze.rows):
        for c in range(maze.cols):
            if len(maze.neighbors(r, c)) == 1:
                dead_ends += 1
    return dead_ends


def run_benchmark(
    sizes: list[int],
    trials: int,
    base_seed: int,
    out_path: Path,
) -> list[dict]:
    """执行多尺寸多轮基准测试并将结果写入 out_path。"""
    rows_out: list[dict] = []

    for size in sizes:
        for trial in range(1, trials + 1):
            seed = base_seed + size * 100 + trial
            for gen_name, gen_fn in GENERATORS:
                rng = random.Random(seed)
                t0 = time.perf_counter()
                maze = gen_fn(size, size, rng=rng)
                gen_ms = (time.perf_counter() - t0) * 1000.0
                dead_ends = count_dead_ends(maze)

                for solver_name, solve_fn in SOLVERS:
                    t1 = time.perf_counter()
                    res = solve_fn(maze)
                    solve_ms = (time.perf_counter() - t1) * 1000.0
                    rows_out.append(
                        {
                            "size": size,
                            "cells": size * size,
                            "trial": trial,
                            "seed": seed,
                            "generator": gen_name,
                            "gen_time_ms": round(gen_ms, 4),
                            "dead_ends": dead_ends,
                            "solver": solver_name,
                            "solve_time_ms": round(solve_ms, 4),
                            "expanded": res.expanded,
                            "path_len": len(res.path),
                            "found": res.found,
                        }
                    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "size",
        "cells",
        "trial",
        "seed",
        "generator",
        "gen_time_ms",
        "dead_ends",
        "solver",
        "solve_time_ms",
        "expanded",
        "path_len",
        "found",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    return rows_out


def print_summary(rows: list[dict]) -> None:
    """按尺寸、生成器和求解器分组打印均值表。"""
    groups: dict[tuple[int, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row["size"], row["generator"], row["solver"])].append(row)

    print(
        "| 尺寸 | 生成器 | 求解器 | 生成均值(ms) | 死胡同均值 | 求解均值(ms) | expanded均值 | 路径长均值 |"
    )
    print("|---:|---|---|---:|---:|---:|---:|---:|")
    for key in sorted(groups.keys()):
        items = groups[key]
        n = len(items)
        size, gen, solver = key
        gen_ms = sum(x["gen_time_ms"] for x in items) / n
        dead_ends = sum(x["dead_ends"] for x in items) / n
        solve_ms = sum(x["solve_time_ms"] for x in items) / n
        expanded = sum(x["expanded"] for x in items) / n
        path_len = sum(x["path_len"] for x in items) / n
        print(
            f"| {size}x{size} | {gen} | {solver} | "
            f"{gen_ms:.2f} | {dead_ends:.1f} | {solve_ms:.2f} | {expanded:.1f} | {path_len:.1f} |"
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="迷宫生成与求解性能对比实验")
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
        default=[10, 20, 50, 100],
        help="测试迷宫边长列表（默认 10 20 50 100）",
    )
    parser.add_argument("--trials", type=int, default=5, help="每个尺寸重复次数（默认 5）")
    parser.add_argument("--seed", type=int, default=2026, help="基础随机种子（默认 2026）")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT_DIR / "docs" / "benchmark.csv",
        help="输出 CSV 路径（默认 docs/benchmark.csv）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rows = run_benchmark(args.sizes, args.trials, args.seed, args.out)
    print(f"已写入 {len(rows)} 条实验记录 -> {args.out}\n")
    print_summary(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
