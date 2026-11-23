"""基于路径压缩和按秩合并的并查集，单次操作均摊 O(alpha(n))。"""
from __future__ import annotations


class UnionFind:
    def __init__(self, n: int):
        """初始化 n 个独立集合，count 记录当前连通分量数。O(n)。"""
        self.n = n
        self.parent = list(range(n))
        self.rank = [0] * n
        self.count = n

    def connected(self, x: int, y: int) -> bool:
        """判断 x 和 y 是否连通。均摊 O(alpha(n))。"""
        return self.find(x) == self.find(y)

    def find(self, x: int) -> int:
        """查找根节点并执行路径压缩。均摊 O(alpha(n))。"""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        """按秩合并两集合；若本已连通返回 False，否则返回 True。均摊 O(alpha(n))。"""
        x = self.find(x)
        y = self.find(y)
        if x == y:
            return False
        # 仅两棵树等高时合并后树高才加 1
        if self.rank[x] == self.rank[y]:
            self.parent[x] = y
            self.rank[y] += 1
        elif self.rank[x] > self.rank[y]:
            self.parent[y] = x
        else:
            self.parent[x] = y
        self.count -= 1
        return True
