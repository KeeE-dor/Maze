# 迷宫系统（数据结构大作业）

2 人团队 · Python + Pygame · 核心数据结构与算法全部手写。

**计划、接口契约、答辩准备 → 见 [项目计划.md](项目计划.md)（先读它，特别是第三节契约）**

> 说明：本项目计划中的核心部分（第 1–5 周全部数据结构、生成/求解算法、Pygame 回放动画交互、正确性验证、性能实验及第 6–7 周非扩展报告素材）已全部完成；第 6 周两项扩展加分项（3D 迷宫建模/复杂度专章、BFS/DFS 同屏对比看板）按要求暂未实现。

## 快速开始

```bash
pip install -r requirements.txt
python main.py                                    # 默认启动 Qt 界面：配置尺寸/生成方式/拆环/泥地 → 生成动画 / 手动走 / 多算法同屏对比
python main.py --pygame                           # Pygame 动画回放 + 键盘交互（R/G/Space/上下键/P/S/Q）
python main.py --pygame --static                  # Pygame 静态渲染
python main.py --console --gen division --loop-ratio 0.1 --mud-ratio 0.2 --seed 42  # 终端模式：6 求解器对比 + 路径高亮
python scripts/verify.py                          # 4 种生成器完美迷宫 + 含环图 BFS<=DFS + 带权图 A*=Dijkstra<=BFS 校验
python scripts/benchmark.py                       # 10/20/50/100 尺寸性能实验，输出 docs/benchmark.csv
python -m pytest                                  # 全量单元测试，无 skip
```

### Qt 界面操作说明
- 启动弹窗可配置迷宫行数/列数（`2~60`）、生成算法（`Kruskal` / `Prim` / `递归回溯` / `递归分割法`）、**拆环比例**（`0~40%`）以及**泥地比例**（`0~50%`，泥地通行代价为 5）。
- **生成动画**：60 FPS 逐堵拆墙（或递归分割筑墙）可视化，支持调速、拖动进度条及 `→` / `←` 单步控制。
- **自己试着走**：方向键或 `W/A/S/D` 移动，实时统计步数与累计地形代价，并与最优步数/最优代价对比。
- **让程序走（算法同屏对比）**：左右面板可自由选择 `BFS`（队列/递归）、`DFS`（递归回溯动画/非递归）、`A*`、`Dijkstra` 任意组合同屏步进对比；按 `→` / `↓` 前进一步，`←` / `↑` 回退一步，`空格` 播放/暂停，`Home` / `End` 跳转起终点。

## 目录与分工

| 路径 | 内容 | 负责人 |
|---|---|---|
| `maze/model.py` | Maze + SolveResult **接口契约**，两人共同维护 | 共同 |
| `maze/ds/union_find.py`、`maze/ds/min_heap.py` | 手写并查集、手写二叉最小堆 | A |
| `maze/ds/stack.py`、`maze/ds/queue.py` | 手写栈、手写循环队列 | B |
| `maze/generators/` | Kruskal、Prim、递归回溯、递归分割法迷宫生成 | A |
| `maze/solvers/` | DFS 两版、BFS 两版、Dijkstra、A*（均用自研数据结构） | B |
| `maze/render/console.py`、`pygame_view.py`、`qt_view.py` | 终端渲染 / Pygame 动画 / PySide6 Qt 交互界面 | B |
| `scripts/verify.py`、`scripts/benchmark.py` | 第 5 周正确性验证三件套 & 性能实验脚本 | A |
| `docs/report-notes.md`、`docs/benchmark.csv` | 实验报告素材、答辩 Q&A 与基准测试数据 | 共同 |
| `tests/` | 单元测试 | 各自 |

## 进度看板（完成打勾）

- [x] 第 1 周：环境 + Git 仓库 + 读懂契约 + model.py 两个练习
- [x] 第 2 周：A→UnionFind + MinHeap；B→Stack/Queue；pytest 全绿 【基石】
- [x] 第 3 周：A→Kruskal；B→DFS 两版；**M1 终端端到端**
- [x] 第 4 周：A→手写 MinHeap（移除 heapq）+ Prim；B→BFS 两版 + Pygame 静态渲染
- [x] 第 5 周：B→Pygame 回放动画 + 交互；A→正确性验证 + 性能实验（CSV）；**M2 可演示**
- [x] 第 6 周（核心部分）：实验报告素材与复杂度整理（`docs/report-notes.md`）※ 扩展加分项暂跳过
- [x] 第 7 周（核心部分）：全量测试 + 验证脚本通过 + 答辩 Q&A 素材完备

> 评审闭环备注：`docs/review-A.md` 中提出的两项问题均已解决——
> `maze/ds/min_heap.py` 已改写为纯手写二叉数组堆（无 `heapq`）；
> `Maze.generate()` 已补充 `rng` 参数并透传至 `kruskal`/`prim` 生成器。

## 契约红线

生成器、求解器、渲染器之间**只通过 `Maze` 与 `SolveResult`（`maze/model.py`）传递**。
修改 `model.py` = 修改契约，必须两人同时在场确认，提交信息注明 `[contract]`。
