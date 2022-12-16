from hm01.graph import Graph
from typing import List
def test_random_graphs_realize_faithfull(context):
    for _ in range(50):
        g = Graph.from_erdos_renyi(100, 0.5)
        rg: List[int] = list(range(40, 60))
        sg1 = g.induced_subgraph(rg, "x")
        sg2 = g.intangible_subgraph(rg, "y").realize(g)
        assert sg1.degree_sequence() == sg2.degree_sequence()
        sg1_v = Graph.from_metis(sg1.as_metis_filepath())
        sg2_v = Graph.from_metis(sg2.as_metis_filepath())
        assert sg1_v.degree_sequence() == sg2_v.degree_sequence()