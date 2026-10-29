# 对 A 侧代码的评审记录（B → A，例会讨论用）

> 背景：我对齐第 2~3 周计划时通读了你的模块，以下按"影响得分/契约/已顺手修复"分类。
> 都不是指责，冲着答辩和报告不丢分来的，例会过一遍就行。

## 一、已顺手修复（不劳你改，知会一下）

`maze/ds/union_find.py` 两处 bug，见提交 `fix(ds): 修复 union_find 计数与按秩合并`：

1. `union()` 成功合并后 `count` 没有减 1。`count` 是 Kruskal 的终止条件依赖
   （连通分量数），也直接挂了 `test_union_find.py` 的两个断言（`count == 4`）。
2. 按秩合并在两棵树**不等高**时也把 rank +1 了——只有等高合并树才会长高。
   不影响正确性但会让 rank 失去"树高上界"的含义，答辩讲按秩合并时容易被抓。

修完后 `test_union_find.py` 的 skip 已删，目前 **46 个测试全绿、0 skip**。

## 二、建议改（影响得分点，例会定个时间）

`maze/ds/min_heap.py` 目前是 `import heapq` 直接包装 push/pop/peek。
**README 和项目计划都写了"核心数据结构与算法全部手写"**，答辩翻代码时
heapq 一眼就会被看到，这个得分点大概率丢。

建议：换成手写数组二叉堆——`push` 尾插 + `_sift_up` 上浮，`pop` 头尾交换 +
`_sift_down` 下沉，复杂度 docstring 写清 O(log n)。总量 40 行左右，
你对堆最熟，你主写我陪跑互讲（正好是第 4 周例会的互讲主题）。
另外现在的版本把原 docstring 里的复杂度说明删掉了，计划要求"完成定义 =
测试通过 + docstring 写明复杂度"，记得补回。

## 三、契约问题（按规矩提出来，不是追究）

`maze/model.py` 新增了 `cell_id()` / `to_point()` / 类方法 `Maze.generate()`，
没有标 `[contract]` 也没经过两人确认——契约红线里 model.py 改动必须两人同场。

两个具体问题：

1. `Maze.generate(rows, cols, method)` **不透传 rng**，而 kruskal/prim 的
   `generate()` 都支持 `rng` 参数。固定种子复现在第 5 周性能实验、
   报告数据、test_solvers 的随机用例里都要用，建议签名加上
   `rng: random.Random | None = None` 并透传。
2. 建议例会时补一次 `[contract]` 提交，把这次新增正式过一遍
   （我这边没意见，`cell_id`/`to_point` 我在 test 里也用得上）。

## 四、小事（不改也行）

- 生成器入口我按契约用 `generate(rows, cols, rng)`，`Maze.generate` 我在
  main.py 里用了，如果按上面加 rng，记得同步。
- `.idea/` 已经随 initial commit 进仓库了，我加的 `.gitignore` 挡不住已跟踪
  文件；要不要 `git rm --cached -r .idea` 由你定（你日常用它，无所谓就留着）。
