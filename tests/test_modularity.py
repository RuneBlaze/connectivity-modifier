from hm01.graph import *

def test_basic_modularity():
    graph = Graph.from_edges([(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)], "root")
    subset = graph.intangible_subgraph([0, 1, 2], "a")
    ls = 2
    L = 6
    ds = 6
    m = (ls/L) - (ds/(2 * L))**2
    assert subset.count_edges(graph) == 2
    assert subset.internal_degree(0, graph) == 1
    assert subset.internal_degree(1, graph) == 2
    assert subset.count_mcd(graph) == 1
    assert graph.modularity_of(subset) == m