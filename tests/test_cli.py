from hm01.graph import Graph
from hm01.cm import MincutRequirement, algorithm_g
from hm01.clusterers.ikc_wrapper import IkcClusterer

def test_mincut_requirement_parsing():
    assert MincutRequirement(1,0,0,0) == MincutRequirement.try_from_str("1log10")
    assert MincutRequirement(0.5,0,0,0) == MincutRequirement.try_from_str("0.5log10")
    assert MincutRequirement(0,0,3,0) == MincutRequirement.try_from_str("3k")
    assert MincutRequirement(1,2,10,0) == MincutRequirement.try_from_str("2mcd+10k+1log10")

    assert MincutRequirement(0,0,3,42) == MincutRequirement.try_from_str("42+3k")
    assert MincutRequirement(1,2,10,42) == MincutRequirement.try_from_str("2mcd+10k+1log10+42")

def test_simple_algorithm_g(context):
    # FIXME: this is a flaky test. With low probability, it fails.
    graph = Graph.from_erdos_renyi(100, 0.8)
    clusterer = IkcClusterer(1)
    clusters = list(clusterer.cluster(graph))
    clusters, label_mapping, tree = algorithm_g(graph, clusters, clusterer, MincutRequirement.most_stringent())
    assert len(clusters) >= 0
    assert tree.root.num_children() >= 0
    assert sum(1 for n in tree.traverse_postorder() if n.extant) == len(clusters)

def test_concrete_graph_same(context):
    for _ in range(10):
        graph = Graph.from_erdos_renyi(100, 0.8)
        rg = list(range(40,60))
        sg = graph.induced_subgraph(rg, "test")
        concrete_sg = graph.intangible_subgraph(rg, "test2").realize(graph)
        assert sg.m() == concrete_sg.m()
        assert sg.n() == concrete_sg.n()
        assert sg.mcd() == concrete_sg.mcd()
        assert sg.find_mincut().cut_size == concrete_sg.find_mincut().cut_size
        for i in range(45,55):
            sg.remove_node(i)
            concrete_sg.remove_node(i)
        assert sg.m() == concrete_sg.m()
        assert sg.n() == concrete_sg.n()
        assert sg.find_mincut().cut_size == concrete_sg.find_mincut().cut_size