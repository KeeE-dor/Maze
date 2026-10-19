"""
演示入口 —— 第 1 周的"走通骨架"示例。

现在：手工构造一个蛇形迷宫，用终端字符画打印（不带路径 / 带路径各一次）。
第 3 周里程碑 M1 之后它会变成：

    import sys
    from maze.generators import kruskal
    from maze.solvers import dfs
    sys.setrecursionlimit(10**6)          # DFS 递归版兜底
    maze = kruskal.generate(15, 25)
    result = dfs.solve_iterative(maze)
    console.print_maze(maze, result.path)
"""
from maze import Maze
from maze.model import DELTA, OPPOSITE
from maze.render import console

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
    """按 OPEN 挖墙，得到一条从 (0,0) 到 (5,0) 的蛇形通道。

    下面这个"算方向 + 两侧同时清位"的内联写法，正是 model.py 里留给你们
    第 1 周实现的 remove_wall_between() 要做的事——实现那个方法后，
    这里的循环体可以替换成一句 m.remove_wall_between(a, b)。
    """
    m = Maze(6, 6)
    for a, b in OPEN:
        dr, dc = b[0] - a[0], b[1] - a[1]
        for d, (ddr, ddc) in DELTA.items():
            if (ddr, ddc) == (dr, dc):
                m.set_wall(a[0], a[1], d, present=False)
                m.set_wall(b[0], b[1], OPPOSITE[d], present=False)
                break
    return m


def demo_path(maze: Maze) -> list[tuple[int, int]]:
    """蛇形通道本身就是路径：起点 + 每一步到达的格子。"""
    return [maze.start] + [b for _, b in OPEN]


def main() -> None:
    maze = carve_demo_maze()

    print("== 第 1 周演示：硬编码迷宫（终端渲染）==")
    console.print_maze(maze)

    print("\n== 带路径高亮（S=起点 E=终点 *=路径）==")
    console.print_maze(maze, demo_path(maze))

    print("\n下一步（见 项目计划.md 第 3 周）：")
    print("  1. 完成 maze/model.py 里两个第 1 周练习（neighbors / remove_wall_between）")
    print("  2. 第 2 周各自实现手写数据结构，pytest 跑绿")
    print("  3. 第 3 周接上 kruskal.generate() + dfs 求解，本文件顶部有示例代码")


if __name__ == "__main__":
    main()
