from dataclasses import dataclass
from typing import Dict, Iterator, List
from hm01.basics import Graph, IntangibleSubgraph
from hm01.types import AbstractCluterer
import leidenalg as la


@dataclass
class LeidenClusterer(AbstractCluterer):
    resolution: float

    def cluster(self, graph: Graph) -> Iterator[IntangibleSubgraph]:
        g = graph.to_igraph()
        partition = la.find_partition(
            g, la.CPMVertexPartition, resolution_parameter=self.resolution
        )
        for i in range(len(partition)):
            nodes = partition[i]
            yield graph.intangible_subgraph_from_compact(nodes, f"{i+1}")

    def from_existing_clustering(self, filepath) -> List[IntangibleSubgraph]:
        # node_id cluster_id format
        clusters: Dict[str, IntangibleSubgraph] = {}
        with open(filepath) as f:
            for line in f:
                node_id, cluster_id = line.split()
                clusters.setdefault(
                    cluster_id, IntangibleSubgraph([], cluster_id)
                ).nodes.append(int(node_id))
        return list(clusters.values())
