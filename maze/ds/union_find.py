"""手写并查集（A 同学 · 第 2 周）—— Kruskal 迷宫生成的核心依赖。

并查集维护"若干互不相交的集合"，两个核心操作：
    find(x)    查 x 所在集合的代表元（根）
    union(x,y) 合并 x、y 所在的两个集合

两个优化（也是答辩考点）：
    1. 路径压缩：find 的路上把沿途节点直接挂到根上，树越来越扁；
    2. 按秩合并：矮树挂到高树下面，防止树退化成链。
    两者合用，单次操作均摊 O(alpha(n))；alpha 是反阿克曼函数，
    只要 n 不超过宇宙原子数，alpha(n) <= 5 —— 实践中当作常数。

学习路线：先读 OI Wiki「并查集」原理，再到 visualgo.net 看动画，然后合上资料自己写。
完成后删掉 tests/test_union_find.py 顶部的 skip 行，pytest 跑绿。
"""
from __future__ import annotations


class UnionFind:
    def __init__(self, n: int):
        """n 个元素 0..n-1，初始互不相通：parent[i] = i，rank 全 0。

        count 记录当前连通分量个数，Kruskal 的终止条件会用到。
        """
        self.n = n
        self.parent = list(range(n))
        self.rank = [0] * n
        self.count = n

    def connected(self, x: int, y: int) -> bool:
        """x、y 是否在同一集合。一行实现：两个 find 的结果比较。"""
        return self.find(x) == self.find(y)

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y) -> bool:
        x = self.find(x)
        y = self.find(y)
        if x == y:
            return False
        if self.rank[x] == self.rank[y]:
            self.parent[x] = y
            self.rank[y] += 1
        elif self.rank[x] > self.rank[y]:
            self.parent[y] = x
            self.rank[x] += 1
        else:
            self.parent[x] = y
            self.rank[y] += 1
        return True