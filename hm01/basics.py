from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
# from hm01.mincut import viecut
from . import mincut

class Graph:
    """Wrapped graph over a networkit graph with an ID label"""
    def __init__(self, data, index):
        self.data = data # nk graph
        self.index = index
    
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

@dataclass
class MincutResult:
    light_partition : List[int] # 0 labeled nodes
    heavy_partition : List[int] # 1 labeled nodes
    cut_size : int

    def realize(self, graph) -> Tuple[Graph, Graph]:
        """Realize the mincut result as a pair of graphs"""
        pass