import networkit as nk

from hm01.graph import *
from hm01.clusterers.leiden_wrapper import LeidenClusterer

# TODO: too much duplicate code
def test_two_k5_two_clusters(context):
    graph = Graph(nk.readGraph("./data/two_k5s.edge_list", nk.Format.EdgeListTabZero), "root")
    for g in [graph, graph.to_realized_subgraph()]:
        clusterer = LeidenClusterer(0.5)
        clusters = list(g.find_clusters(clusterer))
        assert len(clusters) == 2
        assert [c.n() for c in clusters] == [5, 5]
        assert sorted([c.index for c in clusters]) == ["root1", "root2"]

def test_two_k5_two_clusters_non_continuous(context):
    graph = Graph(nk.readGraph("./data/two_k5s_non_continuous.edge_list", nk.Format.EdgeListTabZero, continuous=False), "root")
    for g in [graph, graph.to_realized_subgraph()]:
        graph_nodes = set(g.nodes())
        clusterer = LeidenClusterer(0.5)
        clusters = list(g.find_clusters(clusterer, with_singletons=False))
        cluster_nodes = set.union(*[set(c.subset) for c in clusters])
        assert len(clusters) == 2
        assert cluster_nodes.issubset(graph_nodes)
        assert 999 in cluster_nodes
        assert [c.n() for c in clusters] == [5, 5]
        assert sorted([c.index for c in clusters]) == ["root1", "root2"]

# def test_two_ring_k5_two_clusters(context):
#     graph = Graph(nk.readGraph("./data/ring_two_k5s.edge_list", nk.Format.EdgeListTabZero), "root")
#     clusterer = LeidenClusterer(0.5)
#     clusters = list(graph.find_clusters(clusterer))
#     assert len(clusters) == 2
#     assert [c.n() for c in clusters] == [5, 5]
#     assert sorted([c.index for c in clusters]) == ["root1", "root2"]