from __future__ import annotations
from dataclasses import dataclass
import networkit as nk
from typing import List, Tuple
from . import mincut

class Graph:
    """Wrapped graph over a networkit graph with an ID label"""
    def __init__(self, data, index):
        self.data = data # nk graph
        self.index = index
        self.construct_hydrator()
    
    @staticmethod
    def from_nk(graph, index = ""):
        """Create a wrapped graph from a networkit graph"""
        return Graph(graph, index)

    def n(self):
        """Number of nodes"""
        return self.data.numberOfNodes()
    
    def m(self):
        """Number of edges"""
        return self.data.numberOfEdges()
    
    def mcd(self):
        return -1
    
    def find_clusters(self, clusterer) -> List[Graph]:
        """Find clusters using the given clusterer"""
        return clusterer.cluster(self)
    
    def find_mincut(self):
        """Find a mincut wrapped over Viecut"""
        # TODO: Baqiao implement this
        pass

    def construct_hydrator(self):
        """Hydrator: a mapping from the compacted id to the original id"""
        n = self.n()
        hydrator = [0] * n
        for old_id, new_id in nk.graphtools.getContinuousNodeIds(self.data).items():
            hydrator[new_id] = old_id
        self.hydrator = hydrator

    def induced_subgraph(self, ids, suffix):
        assert suffix != "", "Suffix cannot be empty"
        data = nk.graphtools.subgraphFromNodes(self.data, ids)
        index = self.index + suffix
        return Graph(data, index)
    
    def as_edgelist_filepath(self):
        pass

    def as_metis_filepath(self):
        pass

@dataclass
class MincutResult:
    light_partition : List[int] # 0 labeled nodes
    heavy_partition : List[int] # 1 labeled nodes
    cut_size : int

    def realize(self, graph) -> Tuple[Graph, Graph]:
        """Realize the mincut result as a pair of graphs"""
        pass