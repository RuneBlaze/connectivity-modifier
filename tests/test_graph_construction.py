from hm01.basics import *
import networkit as nk

def test_basic_graph_wrapping():
    data = nk.generators.ErdosRenyiGenerator(100, 0.99).generate()
    graph = Graph.from_nk(data)
    assert graph.n() == 100
    assert graph.m() > 0

def test_basic_subgraph_construction():
    data = nk.generators.ErdosRenyiGenerator(100, 0.99).generate()
    graph = Graph.from_nk(data)
    subgraph = graph.induced_subgraph([50, 55, 51], "a")
    assert subgraph.n() == 3
    assert subgraph.hydrator == [50, 51, 55]