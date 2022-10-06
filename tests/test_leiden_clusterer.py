import networkit as nk

from hm01.basics import *
from hm01.leiden_wrapper import LeidenClusterer

# TODO: too much duplicate code
# def test_two_k5_two_clusters(context):
#     graph = Graph(nk.readGraph("./data/two_k5s.edge_list", nk.Format.EdgeListTabZero), "root")
#     clusterer = LeidenClusterer(0.5)
#     clusters = list(graph.find_clusters(clusterer))
#     assert len(clusters) == 2
#     assert [c.n() for c in clusters] == [5, 5]
#     assert sorted([c.index for c in clusters]) == ["root1", "root2"]

# def test_two_k5_two_clusters_non_continuous(context):
#     graph = Graph(nk.readGraph("./data/two_k5s_non_continuous.edge_list", nk.Format.EdgeListTabZero, continuous=False), "root")
#     clusterer = LeidenClusterer(0.5)
#     clusters = list(graph.find_clusters(clusterer))
#     assert len(clusters) == 2
#     assert [c.n() for c in clusters] == [5, 5]
#     assert sorted([c.index for c in clusters]) == ["root1", "root2"]

# def test_two_ring_k5_two_clusters(context):
#     graph = Graph(nk.readGraph("./data/ring_two_k5s.edge_list", nk.Format.EdgeListTabZero), "root")
#     clusterer = LeidenClusterer(0.5)
#     clusters = list(graph.find_clusters(clusterer))
#     assert len(clusters) == 2
#     assert [c.n() for c in clusters] == [5, 5]
#     assert sorted([c.index for c in clusters]) == ["root1", "root2"]