from hm01.basics import *
import networkit as nk

def test_basic_graph_wrapping():
    data = nk.generators.ErdosRenyiGenerator(100, 0.99).generate()
    graph = Graph.from_nk(data)
    assert graph.n() == 100
    assert graph.m() > 0
    assert 100 > graph.mcd() > 50

def test_basic_subgraph_construction():
    data = nk.generators.ErdosRenyiGenerator(100, 0.99).generate()
    graph = Graph.from_nk(data)
    subgraph = graph.induced_subgraph([50, 55, 51], "a")
    assert subgraph.n() == 3
    assert subgraph.hydrator == [50, 51, 55]

def test_basic_graph_format_conversion(context):
    data = nk.generators.ErdosRenyiGenerator(100, 0.99).generate()
    graph = Graph.from_nk(data)
    assert graph.as_compact_edgelist_filepath() is not None
    assert graph.as_metis_filepath() is not None
    # both files should also be readable and not empty
    assert os.path.getsize(graph.as_compact_edgelist_filepath()) > 0
    assert os.path.getsize(graph.as_metis_filepath()) > 0