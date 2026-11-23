"""UnionFind 单元测试。"""
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
    assert uf.union(0, 1) is False


def test_transitivity():
    uf = UnionFind(6)
    uf.union(0, 2)
    uf.union(2, 4)
    assert uf.connected(0, 4)


def test_path_compression_flattens_tree():
    uf = UnionFind(8)
    for i in range(7):
        uf.union(i, i + 1)
    root = uf.find(3)
    assert uf.parent[3] == root


def test_two_groups_stay_separate():
    uf = UnionFind(6)
    uf.union(0, 1)
    uf.union(2, 3)
    assert not uf.connected(0, 2)
    assert uf.count == 4
