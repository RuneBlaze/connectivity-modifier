from __future__ import annotations
from dataclasses import dataclass
import networkit as nk
from typing import List, Tuple
import os
from . import mincut
from .context import context

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
        return min(self.data.degree(n) for n in self.data.iterNodes())
    
    def find_clusters(self, clusterer) -> List[Graph]:
        """Find clusters using the given clusterer"""
        return clusterer.cluster(self)
    
    def find_mincut(self):
        """Find a mincut wrapped over Viecut"""
        return mincut.viecut(self)
    
    def cut_by_mincut(self, mincut_res) -> Tuple[Graph, Graph]:
        """Cut the graph by the mincut result"""
        light = self.induced_subgraph(mincut_res.light_partition, "a")
        heavy = self.induced_subgraph(mincut_res.heavy_partition, "b")
        return light, heavy

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
    
    def as_compact_edgelist_filepath(self):
        """Get a filepath to the graph as a compact/continuous edgelist file"""
        p = context.request_graph_related_path(self, "edgelist")
        nk.graphio.writeGraph(self.data, p, nk.Format.EdgeListSpaceOne)
        return p

    def as_metis_filepath(self):
        """Get a filepath to the graph to a (continuous) METIS file"""
        p = context.request_graph_related_path(self, "metis")
        nk.graphio.writeGraph(self.data, p, nk.Format.METIS)
        return p
    
    def nodes(self):
        """Iterate over the nodes"""
        return self.data.iterNodes()
    
    @staticmethod
    def from_space_edgelist(filepath: str, index=""):
        return Graph(nk.graphio.readGraph(filepath, nk.Format.EdgeListSpaceZero), index)

    @staticmethod
    def from_erdos_renyi(n, p, index=""):
        return Graph(nk.generators.ErdosRenyiGenerator(n, p).generate(), index)