from hm01.graph import *
from hm01.mincut_requirement import MincutRequirement
from hm01.pruner import prune_graph
from hm01.clusterers.ikc_wrapper import IkcClusterer

def test_not_pruning():
    clique = Graph.from_clique(10)
    assert clique.n() == 10
    assert clique.m() == 45
    assert clique.mcd() == 9
    clusterer = IkcClusterer(5)
    requirement = MincutRequirement.from_constant(3)
    num_pruned = prune_graph(clique, requirement, clusterer)
    assert num_pruned == 0

def test_pruning():
    stright_line = Graph.from_straight_line(10)
    assert stright_line.n() == 10
    assert stright_line.m() == 9
    assert stright_line.mcd() == 1
    clusterer = IkcClusterer(5)
    requirement = MincutRequirement.try_from_str("1log10")
    num_pruned = prune_graph(stright_line, requirement, clusterer)
    assert num_pruned == 1

def test_pruning_more_complex():
    for n in range(9, 15):
        graph = Graph.from_straight_line(n)
        n_before = graph.n()
        clusterer = IkcClusterer(5)
        requirement = MincutRequirement.try_from_str("1log10")
        num_pruned = prune_graph(graph, requirement, clusterer)
        n_after = graph.n()
        assert num_pruned == n - 9
        assert n_after == n_before - num_pruned