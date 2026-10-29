"""UnionFind 的单元测试（A 同学第 2 周实现 union_find.py 后删除顶部 skip 行）。

进阶练习（可选，答辩亮点）：和"朴素对拍"——用 set-of-sets 模拟同样的操作序列，
随机做上千次 union / connected，手写版的结果必须和朴素版完全一致。
"""
from maze.ds.union_find import UnionFind


def test_initially_all_separate():
    uf = UnionFind(5)
    assert uf.count == 5
    assert not uf.connected(0, 1)


def test_union_merges_and_reports():
    uf = UnionFind(5)
    assert uf.union(0, 1) is True
    assert uf.connected(0, 1)
    assert uf.count == 4
    assert uf.union(0, 1) is False  # 已连通：再 union 返回 False 且 count 不变


def test_transitivity():
    uf = UnionFind(6)
    uf.union(0, 2)
    uf.union(2, 4)
    assert uf.connected(0, 4)


def test_path_compression_flattens_tree():
    uf = UnionFind(8)
    for i in range(7):  # 串成一条链：0-1-2-...-7
        uf.union(i, i + 1)
    root = uf.find(3)   # 这次 find 应把 3 直接挂到根上
    assert uf.parent[3] == root


def test_two_groups_stay_separate():
    uf = UnionFind(6)
    uf.union(0, 1)
    uf.union(2, 3)
    assert not uf.connected(0, 2)
    assert uf.count == 4
