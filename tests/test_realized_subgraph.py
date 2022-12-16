from hm01.graph import Graph, RealizedSubgraph
def test_conversion_works():
    graph = Graph.from_erdos_renyi(10, 0.6)
    sg = graph.to_realized_subgraph()
    assert graph.n() == sg.n()
    assert graph.m() == sg.m()
    sg = graph.intangible_subgraph([2,5,8,9], "a").realize(graph)
    sg.recompact()
    for k, v in sg.inv.items():
        assert sg.hydrator[v] == k
    assert len(sg.hydrator) == len(sg.inv)