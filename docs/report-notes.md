# 实验报告与答辩核心素材（非扩展部分）

> 本文档对应《项目计划.md》第七节（实验报告结构）与第八节（答辩 Q&A 清单），汇总架构设计、复杂度、实测性能数据与正确性验证结果。说明：本次范围**不包含**加分扩展项（3D 建模/复杂度专章、同屏对比看板）。

---

## 1. 总体设计与模块依赖

```text
UnionFind / MinHeap / Stack / Queue      <- 底层数据结构，零依赖，不含任何迷宫概念
        ^                    ^
generators (A: UF+Heap)   solvers (B: Stack+Queue)
        \----> maze/model.py (Maze + SolveResult) <----/
                             |
                             v
            render/console.py · pygame_view.py (通过回调注入与算法解耦)
```

- **核心契约（`maze/model.py`）**：
  - `Maze.walls[r][c]` 采用 4 位掩码表示四面墙：`N=1, E=2, S=4, W=8`，全墙初值 `15`。
  - 拆墙使用 `remove_wall_between(a, b)` 同时清除相邻两格对应相反方向位，确保两侧状态一致。
  - `SolveResult` 统一返回 `path`、`visited_order`、`found`、`expanded`。

---

## 2. 数据结构与算法复杂度汇总

| 模块 | 实现位置 | 核心机制 | 时间复杂度 | 空间复杂度 |
|---|---|---|---|---|
| 并查集 `UnionFind` | `maze/ds/union_find.py` | 路径压缩 + 按秩合并 | 均摊 $O(\alpha(n))$ | $O(n)$ |
| 最小堆 `MinHeap` | `maze/ds/min_heap.py` | 0 下标数组二叉堆（`_sift_up` / `_sift_down`） | `push/pop` $O(\log n)$，`peek` $O(1)$ | $O(n)$ |
| 栈 `Stack` | `maze/ds/stack.py` | 动态数组尾部压栈/弹栈 | 均摊 $O(1)$ | $O(n)$ |
| 循环队列 `Queue` | `maze/ds/queue.py` | `_head + _size` 取模回绕，满时翻倍搬迁 | 出入队均摊 $O(1)$ | $O(n)$ |
| Kruskal 生成 | `maze/generators/kruskal.py` | 内部边随机赋权入堆 + `UnionFind` 判环 | $O(E \log E) = O(V \log V)$ | $O(V)$ |
| Prim 生成 | `maze/generators/prim.py` | 从 `(0, 0)` 生长，`MinHeap` 维护 frontier 边 | $O(E \log E) = O(V \log V)$ | $O(V)$ |
| DFS 递归 / 迭代 | `maze/solvers/dfs.py` | 调用栈递归 / 手写 `Stack` + `parent` 回溯 | $O(V + E) = O(V)$ | $O(V)$ |
| BFS 队列 / 按层递归 | `maze/solvers/bfs.py` | 手写 `Queue` / 按层收集 `next_frontier` 递归 | $O(V + E) = O(V)$ | $O(V)$ |

*(注：网格图中顶点数 $V = \text{rows} \times \text{cols}$，边数 $E \le 2V$。)*

---

## 3. 第 5 周正确性验证结果（`scripts/verify.py`）

执行 `python scripts/verify.py` 全部通过（共 34 组验证用例）：
1. **完美迷宫验证**：对 `5×5`、`10×10`、`20×20`、`30×30` × `Kruskal/Prim` × 3 组种子（共 24 组），确认外墙封闭、内部墙对称、拆墙数严格等于 `rows * cols - 1`，且手写 `UnionFind` 检验无环、连通分量数为 `1`。
2. **求解路径合法性**：对 4 种求解器用 `has_wall` 双向核查每一步均不穿墙、首尾与 `start/end` 一致、无重复节点。
3. **含环非完美迷宫交叉验证**：在 `15×15` 迷宫上额外随机拆掉 35 堵内部墙构造 10 组含环迷宫，全部满足 `len(BFS) <= len(DFS)`，且 **10/10 组** 中 `BFS` 路径严格短于 `DFS`。

---

## 4. 第 5 周性能实验实测数据（`scripts/benchmark.py` → `docs/benchmark.csv`）

测试参数：尺寸 `10 / 20 / 50 / 100`，每个尺寸重复 `5` 次试验（共 160 条记录），环境 Windows Python 3.13.9：

| 尺寸 | 生成器 | 求解器 | 生成均值 (ms) | 死胡同均值 | 求解均值 (ms) | expanded 均值 | 路径长均值 |
|---:|---|---|---:|---:|---:|---:|---:|
| 10x10 | kruskal | bfs_queue | 0.63 | 30.0 | 0.25 | 81.0 | 25.0 |
| 10x10 | kruskal | bfs_recursive | 0.63 | 30.0 | 0.20 | 81.0 | 25.0 |
| 10x10 | kruskal | dfs_iterative | 0.63 | 30.0 | 0.18 | 65.2 | 25.0 |
| 10x10 | kruskal | dfs_recursive | 0.63 | 30.0 | 0.13 | 59.2 | 25.0 |
| 10x10 | prim | bfs_queue | 0.64 | 29.6 | 0.27 | 87.6 | 25.8 |
| 10x10 | prim | bfs_recursive | 0.64 | 29.6 | 0.25 | 87.6 | 25.8 |
| 10x10 | prim | dfs_iterative | 0.64 | 29.6 | 0.16 | 62.4 | 25.8 |
| 10x10 | prim | dfs_recursive | 0.64 | 29.6 | 0.15 | 63.2 | 25.8 |
| 20x20 | kruskal | bfs_queue | 3.19 | 119.8 | 1.67 | 359.8 | 60.2 |
| 20x20 | kruskal | bfs_recursive | 3.19 | 119.8 | 1.07 | 359.8 | 60.2 |
| 20x20 | kruskal | dfs_iterative | 3.19 | 119.8 | 0.59 | 202.0 | 60.2 |
| 20x20 | kruskal | dfs_recursive | 3.19 | 119.8 | 0.70 | 257.2 | 60.2 |
| 20x20 | prim | bfs_queue | 3.72 | 125.2 | 1.16 | 352.8 | 55.0 |
| 20x20 | prim | bfs_recursive | 3.72 | 125.2 | 0.85 | 352.8 | 55.0 |
| 20x20 | prim | dfs_iterative | 3.72 | 125.2 | 0.61 | 233.4 | 55.0 |
| 20x20 | prim | dfs_recursive | 3.72 | 125.2 | 0.51 | 220.8 | 55.0 |
| 50x50 | kruskal | bfs_queue | 27.85 | 756.0 | 7.17 | 2230.0 | 180.2 |
| 50x50 | kruskal | bfs_recursive | 27.85 | 756.0 | 7.03 | 2230.0 | 180.2 |
| 50x50 | kruskal | dfs_iterative | 27.85 | 756.0 | 4.19 | 1585.8 | 180.2 |
| 50x50 | kruskal | dfs_recursive | 27.85 | 756.0 | 3.06 | 1094.2 | 180.2 |
| 50x50 | prim | bfs_queue | 28.72 | 748.4 | 7.07 | 2103.6 | 167.4 |
| 50x50 | prim | bfs_recursive | 28.72 | 748.4 | 6.21 | 2103.6 | 167.4 |
| 50x50 | prim | dfs_iterative | 28.72 | 748.4 | 3.45 | 1319.0 | 167.4 |
| 50x50 | prim | dfs_recursive | 28.72 | 748.4 | 3.34 | 1347.6 | 167.4 |
| 100x100 | kruskal | bfs_queue | 140.05 | 3050.8 | 25.48 | 8037.4 | 409.4 |
| 100x100 | kruskal | bfs_recursive | 140.05 | 3050.8 | 23.37 | 8037.4 | 409.4 |
| 100x100 | kruskal | dfs_iterative | 140.05 | 3050.8 | 15.76 | 5672.6 | 409.4 |
| 100x100 | kruskal | dfs_recursive | 140.05 | 3050.8 | 13.31 | 4736.6 | 409.4 |
| 100x100 | prim | bfs_queue | 141.39 | 3048.0 | 30.93 | 9446.8 | 387.0 |
| 100x100 | prim | bfs_recursive | 141.39 | 3048.0 | 28.09 | 9446.8 | 387.0 |
| 100x100 | prim | dfs_iterative | 141.39 | 3048.0 | 14.06 | 4996.2 | 387.0 |
| 100x100 | prim | dfs_recursive | 141.39 | 3048.0 | 15.97 | 5390.4 | 387.0 |

**关键现象分析**：
- `100×100`（10,000 格）下 Kruskal 与 Prim 生成耗时均约 140 ms，符合 $O(V \log V)$ 渐近增长特征。
- 同一完美迷宫上四版求解器路径长完全一致（树中两点路径唯一）；但在 `expanded` 上，BFS 往往高于 DFS（约 8000~9400 vs 4700~5700），原因是完美迷宫无捷径、终点在右下角，BFS 需要均匀向外铺满“距起点 $\le d$”的全部等距层，而 DFS 沿某条主干深入遇到目标即提前短路。

---

## 5. 答辩 Q&A 准备清单（对应计划书第八节 1–9 题）

1. **并查集路径压缩 + 按秩合并的作用与复杂度**：
   - 路径压缩把 `find` 沿途节点直接挂到根节点上压扁树高；按秩合并只把矮树挂到高树下（仅等高时 `rank + 1`），防止树退化成链。两者合用均摊复杂度 $O(\alpha(n))$，实际工程尺度下 $\alpha(n) \le 5$。
2. **为什么 Kruskal 拆 `rows * cols - 1` 堵墙必得完美迷宫**：
   - 初始共 $V = \text{rows} \times \text{cols}$ 个连通分量；每次仅合并两个不连通分量且不成环，拆 $V-1$ 条边后连通分量恰好减为 $1$，构成图的生成树，因此任意两点间有且仅有一条简单路径。
3. **BFS 为什么保证最短路而 DFS 不保证**：
   - BFS 按边数层序推进，首次访问到某节点时的层数即最短距离；反证：若存在更短路径，则其前驱在更早层就应先扩展到终点。DFS 只顾纵深探索，在含环图中可能先走通一条绕远路（见 `tests/test_solvers.py::test_bfs_finds_shortest_path_on_cyclic_maze` 的 `4×4` 7 格 vs 11 格反例）。
4. **最小堆 `push / pop` 的 `O(log n)` 原理与实现**：
   - 二叉堆是完全二叉树，树高 $\lfloor \log_2 n \rfloor$。`push` 尾插后执行 `_sift_up` 与父节点 `(i-1)//2` 比较交换上浮；`pop` 取堆顶、尾元素补至索引 `0` 后执行 `_sift_down` 与较小子节点 `2i+1 / 2i+2` 比较下沉，两者最多各移动树高步。
5. **位掩码 vs 邻接表的取舍**：
   - 位掩码每格只存 1 个整数（4 bit 表示 `N/E/S/W` 墙），内存紧凑、缓存局部性好、`has_wall/set_wall` 语义直接；邻接表更适合不规则拓扑或带非统一边权的稀疏图。
6. **递归 BFS 的实现与和队列版的本质差异**：
   - 采用**按层递归**：`_layer(frontier)` 遍历当前层节点并把所有未访问邻居收入 `next_frontier`，再递归 `_layer(next_frontier)`。两者访问序与 `expanded` 完全一致，差异在于队列版将 frontier 存在显式 `Queue` 中，而递归版由函数调用栈维护层状态，递归深度等于最短路层数。
7. **手写 Stack/Queue 与 Python `list`/`deque` 的差异**：
   - 课程手写的价值在于明确数据结构契约、边界异常（空容器 `IndexError`）与底层代价控制（例如避免 `list.pop(0)` 的 $O(n)$ 搬移，改用环形数组取模回绕 + 翻倍扩容实现均摊 $O(1)$ 循环队列）。
8. **BFS 与 DFS 的 `expanded` 差异**：
   - 完美迷宫中终点位于对角角落，BFS 必须扩展完所有曼哈顿/路径距离小于终点的节点，往往覆盖 80%–95% 网格；DFS 运气较好时约扩展 45%–57% 即触达终点，两者均受迷宫分支走向影响。
9. **DFS 递归版在大迷宫的局限**：
   - 调用栈深度取决于迷宫最长探索深度（最坏可达 $O(\text{rows}\times\text{cols})$），受 Python 默认递归深度上限（1000）及栈帧内存限制；虽然可通过 `sys.setrecursionlimit(10**6)` 放宽 Python 层限制，但工程上仍可能受 C 原生栈大小约束，因此大迷宫优先用基于显式 `Stack` 的非递归版。
