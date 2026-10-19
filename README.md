# 迷宫系统（数据结构大作业）

2 人团队 · Python + Pygame · 核心数据结构与算法全部手写。

**计划、接口契约、答辩准备 → 见 [项目计划.md](项目计划.md)（先读它，特别是第三节契约）**

## 快速开始

```bash
pip install -r requirements.txt
python main.py        # 第 1 周演示：终端迷宫（现在就能跑）
python -m pytest      # 测试：test_example 全绿；stack/union_find 处于 skip（待实现）
```

## 目录与分工

| 路径 | 内容 | 负责人 |
|---|---|---|
| `maze/model.py` | Maze + SolveResult **接口契约**，两人共同维护 | 共同 |
| `maze/ds/union_find.py`、`maze/ds/min_heap.py` | 手写并查集、最小堆 | A |
| `maze/ds/stack.py`、`maze/ds/queue.py` | 手写栈、队列 | B |
| `maze/generators/` | Kruskal、Prim 迷宫生成 | A |
| `maze/solvers/` | DFS 两版、BFS 两版 | B |
| `maze/render/console.py`（已实现）、`maze/render/pygame_view.py` | 终端渲染 / Pygame 动画 | B |
| `tests/` | 单元测试，谁写的模块谁补测试 | 各自 |

## 进度看板（完成打勾）

- [ ] 第 1 周：环境 + Git 仓库 + 读懂契约 + model.py 两个练习
- [ ] 第 2 周：A→UnionFind；B→Stack/Queue；pytest 全绿 【基石】
- [ ] 第 3 周：A→Kruskal；B→DFS 两版；**M1 终端端到端**
- [ ] 第 4 周：A→MinHeap 完善 + Prim；B→BFS 两版 + Pygame 静态
- [ ] 第 5 周：B→回放动画 + 交互；A→正确性验证 + 性能实验；**M2 可演示**
- [ ] 第 6 周：加分项 + 报告初稿（周三检查点）
- [ ] 第 7 周：功能冻结 + 报告/PPT 定稿 + 互讲模拟答辩

## 契约红线

生成器、求解器、渲染器之间**只通过 `Maze` 与 `SolveResult`（`maze/model.py`）传递**。
修改 `model.py` = 修改契约，必须两人同时在场确认，提交信息注明 `[contract]`。
