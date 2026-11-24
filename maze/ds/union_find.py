"""基于路径压缩和按秩合并的并查集（Union-Find），单次操作均摊 O(alpha(n))。"""
from __future__ import annotations


class UnionFind:
    def __init__(self, n: int):
        """初始化 n 个独立集合（编号 0 到 n-1），初始各自自成一派。O(n)。"""
        self.n = n
        # parent[i] 表示元素 i 的父节点；初始时每个元素的父节点都是自己（即自己是根）
        self.parent = list(range(n))
        # rank[i] 记录以 i 为根的树的大致高度上界，用于按秩合并时避免树退化成链
        self.rank = [0] * n
        # count 记录当前共有多少个互不连通的集合；每次成功合并会减 1
        self.count = n

    def connected(self, x: int, y: int) -> bool:
        """判断元素 x 和 y 是否在同一个集合（即根节点是否相同）。均摊 O(alpha(n))。"""
        return self.find(x) == self.find(y)

    def find(self, x: int) -> int:
        """查找元素 x 所在集合的根节点，并在回溯时做路径压缩。均摊 O(alpha(n))。"""
        if self.parent[x] != x:
            # 递归找到真正的根节点，并把沿途经过的所有节点直接挂到根节点下面（扁平化）
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        """合并 x 和 y 所在的集合；若原本就连通则返回 False，否则返回 True。均摊 O(alpha(n))。"""
        x = self.find(x)
        y = self.find(y)
        if x == y:
            # 根节点相同，说明已经在一个集合里了，不需要合并
            return False

        # 按秩合并：总是把矮树挂到高树下面，这样合并后整棵树的高度不会增加
        # 只有两棵树一样高时，合并后新树高度才会比原来多 1
        if self.rank[x] == self.rank[y]:
            self.parent[x] = y
            self.rank[y] += 1
        elif self.rank[x] > self.rank[y]:
            self.parent[y] = x
        else:
            self.parent[x] = y

        self.count -= 1  # 两个集合合二为一，总集合数减 1
        return True
