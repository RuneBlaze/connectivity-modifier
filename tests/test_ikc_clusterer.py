import networkit as nk

from hm01.basics import *
from hm01.ikc_wrapper import IkcClusterer


def test_basic_ikc_clustering_0():
    data = nk.readGraph("./data/two_k5s.edge_list", nk.Format.EdgeListTabZero)
    graph = Graph(data, "2a")
    k = 5
    clusterer_name = "IKC"
    graph_arr = graph.find_clusters(IkcClusterer(k, clusterer_name))
    cluster_id_arr = ["2a1", "2a2", "2a3", "2a4", "2a5", "2a6", "2a7", "2a8", "2a9", "2a10"]
    for current_graph in graph_arr:
        cluster_id_arr.remove(current_graph.index)
    assert len(cluster_id_arr) == 0

def test_basic_ikc_clustering_1():
    data = nk.readGraph("./data/two_k5s.edge_list", nk.Format.EdgeListTabZero)
    graph = Graph(data, "1b")
    k = 4
    clusterer_name = "IKC"
    graph_arr = graph.find_clusters(IkcClusterer(k, clusterer_name))
    cluster_id_arr = ["1b1", "1b2"]
    for current_graph in graph_arr:
        cluster_id_arr.remove(current_graph.index)
    assert len(cluster_id_arr) == 0
    assert graph_arr[0].n() == 5
    assert graph_arr[1].n() == 5
