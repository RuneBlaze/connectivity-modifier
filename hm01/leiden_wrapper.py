from dataclasses import dataclass
from typing import Iterator
from hm01.basics import Graph, IntangibleSubgraph
from hm01.types import AbstractCluterer
import leidenalg as la

@dataclass
class LeidenClusterer(AbstractCluterer):
    resolution : float

    def cluster(self, graph: Graph) -> Iterator[IntangibleSubgraph]:
        g = graph.to_igraph()
        partition = la.find_partition(g, la.CPMVertexPartition, resolution_parameter=self.resolution)
        for i in range(len(partition)):
            nodes = partition[i]
            yield graph.intangible_subgraph_from_compact(nodes, f"{i+1}")