"""
演示入口 —— 里程碑 M1（第 3 周）：一条命令完成 生成 → DFS 求解 → 终端高亮。

运行：python main.py
第 4 周在此基础上接入 BFS 与 Pygame 静态渲染。

保留的调试设施（tests/test_solvers.py 依赖，勿删）：
    carve_demo_maze()  硬编码 6×6 蛇形迷宫（单走廊，路径唯一，测试用）
    demo_path()        蛇形走廊本身
"""
import sys

from maze import Maze
from maze.render import console
from maze.solvers import dfs

sys.setrecursionlimit(10**6)  # DFS 递归版兜底：调用栈深度 = 迷宫深度

# 蛇形迷宫要打通的相邻格对：(0,0) 一路走到 (5,0)
OPEN = [
    ((0, 0), (0, 1)), ((0, 1), (0, 2)), ((0, 2), (0, 3)), ((0, 3), (0, 4)), ((0, 4), (0, 5)),
    ((0, 5), (1, 5)), ((1, 5), (2, 5)),
    ((2, 5), (2, 4)), ((2, 4), (2, 3)), ((2, 3), (2, 2)), ((2, 2), (2, 1)), ((2, 1), (2, 0)),
    ((2, 0), (3, 0)), ((3, 0), (4, 0)),
    ((4, 0), (4, 1)), ((4, 1), (4, 2)), ((4, 2), (4, 3)), ((4, 3), (4, 4)), ((4, 4), (4, 5)),
    ((4, 5), (5, 5)), ((5, 5), (5, 4)), ((5, 4), (5, 3)), ((5, 3), (5, 2)), ((5, 2), (5, 1)),
    ((5, 1), (5, 0)),
]


def carve_demo_maze() -> Maze:
    """按 OPEN 挖墙，得到一条从 (0,0) 到 (5,0) 的蛇形通道（测试用，勿删）。"""
    m = Maze(6, 6)
    for a, b in OPEN:
        m.remove_wall_between(a, b)
    return m


def demo_path(maze: Maze) -> list[tuple[int, int]]:
    """蛇形通道本身就是路径：起点 + 每一步到达的格子（测试用，勿删）。"""
    return [maze.start] + [b for _, b in OPEN]


def main() -> None:
    maze = Maze.generate(15, 25, "kruskal")

    print("== M1 演示：Kruskal 生成 15×25（终端渲染）==")
    console.print_maze(maze)

    result = dfs.solve_iterative(maze)
    print(f"\n== DFS 非递归求解（expanded={result.expanded}, "
          f"路径长={len(result.path)}）==")
    console.print_maze(maze, result.path)

    r2 = dfs.solve_recursive(maze)
    assert r2.path == result.path, "完美迷宫上两版 DFS 的 path 必须一致"
    print(f"\n== 自检：递归版 path 与非递归版完全一致 "
          f"(expanded={r2.expanded}) ==")


if __name__ == "__main__":
    main()
