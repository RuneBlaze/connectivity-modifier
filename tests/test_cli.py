from hm01.basics import Graph
from hm01.cut_clusters import MincutRequirement, algorithm_g
from hm01.ikc_wrapper import IkcClusterer

def test_mincut_requirement_parsing():
    assert MincutRequirement(1,0,0,0) == MincutRequirement.try_from_str("1log10")
    assert MincutRequirement(0.5,0,0,0) == MincutRequirement.try_from_str("0.5log10")
    assert MincutRequirement(0,0,3,0) == MincutRequirement.try_from_str("3k")
    assert MincutRequirement(1,2,10,0) == MincutRequirement.try_from_str("2mcd+10k+1log10")

    assert MincutRequirement(0,0,3,42) == MincutRequirement.try_from_str("42+3k")
    assert MincutRequirement(1,2,10,42) == MincutRequirement.try_from_str("2mcd+10k+1log10+42")

def test_simple_algorithm_g(context):
    graph = Graph.from_erdos_renyi(100, 0.3)
    clusterer = IkcClusterer(1)
    clusters = list(clusterer.cluster(graph))
    clusters, label_mapping, tree = algorithm_g(graph, clusters, clusterer, MincutRequirement.most_stringent())
    assert len(clusters) >= 0
    assert tree.root.num_children() >= 0
    assert sum(1 for n in tree.traverse_postorder() if n.extant) == len(clusters)