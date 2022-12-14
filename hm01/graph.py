from __future__ import annotations
from dataclasses import dataclass
from typing_extensions import Self
import networkit as nk
from typing import Dict, Iterator, List, Sequence, Tuple

from hm01.clusterers.abstract_clusterer import AbstractClusterer
from . import mincut
from .context import context
from structlog import get_logger
from functools import cache, cached_property

log = get_logger()


class Graph:
    """Wrapped graph over a networkit graph with an ID label"""

    def __init__(self, data, index):
        self._data = data  # nk graph
        self.index = index
        self.construct_hydrator()

    @staticmethod
    def from_nk(graph, index=""):
        """Create a wrapped graph from a networkit graph"""
        return Graph(graph, index)

    @staticmethod
    def from_edgelist(path):
        """Read a graph from an edgelist file"""
        edgelist_reader = nk.graphio.EdgeListReader("\t", 0)
        nk_graph = edgelist_reader.read(path)
        return Graph.from_nk(nk_graph)

    def n(self) -> int:
        """Number of nodes"""
        return self._data.numberOfNodes()

    def m(self) -> int:
        """Number of edges"""
        return self._data.numberOfEdges()

    @cache
    def mcd(self) -> int:
        if self.n() == 0:
            return 0
        return min(self._data.degree(n) for n in self._data.iterNodes())

    def find_clusters(
        self, clusterer: AbstractClusterer, with_singletons: bool =True
    ) -> Iterator[IntangibleSubgraph]:
        """Find clusters using the given clusterer"""
        log.info(
            f"Finding clusters using clusterer",
            id=self.index,
            n=self.n(),
            m=self.m(),
            clusterer=clusterer,
        )
        if with_singletons:
            return clusterer.cluster(self)
        else:
            return clusterer.cluster_without_singletons(self)

    def find_mincut(self) -> mincut.MincutResult:
        """Find a mincut wrapped over Viecut"""
        return mincut.viecut(self)

    def neighbors(self, u):
        yield from self._data.iterNeighbors(u)

    def remove_node(self, u):
        self._data.removeNode(u)

    def cut_by_mincut(self, mincut_res: mincut.MincutResult) -> Tuple[Graph, Graph]:
        """Cut the graph by the mincut result"""
        light = self.induced_subgraph(mincut_res.light_partition, "a")
        heavy = self.induced_subgraph(mincut_res.heavy_partition, "b")
        return light, heavy

    def construct_hydrator(self):
        """Hydrator: a mapping from the compacted id to the original id"""
        n = self.n()
        hydrator = [0] * n
        continuous_ids = nk.graphtools.getContinuousNodeIds(self._data).items()
        assert len(continuous_ids) == n, f"Expected {n} ids, got {len(continuous_ids)}"
        for old_id, new_id in continuous_ids:
            hydrator[new_id] = old_id
        self.hydrator = hydrator

    def induced_subgraph(self, ids: List[int], suffix: str):
        assert suffix != "", "Suffix cannot be empty"
        data = nk.graphtools.subgraphFromNodes(self._data, ids)
        index = self.index + suffix
        return Graph(data, index)

    def induced_subgraph_from_compact(self, ids: List[int], suffix: str):
        return self.induced_subgraph([self.hydrator[i] for i in ids], suffix)

    def intangible_subgraph(self, nodes: List[int], suffix: str):
        return IntangibleSubgraph(nodes, self.index + suffix)

    def intangible_subgraph_from_compact(self, ids: List[int], suffix: str):
        """Create an intangible subgraph from a list of ids that represent nodes in the compacted (i.e., made continuous) graph
        """
        return self.intangible_subgraph([self.hydrator[i] for i in ids], suffix)

    def as_compact_edgelist_filepath(self):
        """Get a filepath to the graph as a compact/continuous edgelist file"""
        p = context.request_graph_related_path(self, "edgelist")
        nk.graphio.writeGraph(self._data, p, nk.Format.EdgeListSpaceOne)
        return p

    def degree(self, u):
        return self._data.degree(u)

    def as_metis_filepath(self):
        """Get a filepath to the graph to a (continuous) METIS file"""
        p = context.request_graph_related_path(self, "metis")
        nk.graphio.writeGraph(self._data, p, nk.Format.METIS)
        return p

    def nodes(self):
        """Iterate over the nodes"""
        return self._data.iterNodes()

    def modularity_of(self, g: IntangibleSubgraph) -> float:
        """calculate the modularity of the subset `g` with respect to `self`"""
        ls = g.count_edges(self)
        big_l = self.m()
        ds = sum(self._data.degree(n) for n in g.subset)
        return (ls / big_l) - (ds / (2 * big_l)) ** 2

    @staticmethod
    def from_space_edgelist(filepath: str, index=""):
        return Graph(nk.graphio.readGraph(filepath, nk.Format.EdgeListSpaceZero), index)

    @staticmethod
    def from_erdos_renyi(n, p, index=""):
        return Graph(nk.generators.ErdosRenyiGenerator(n, p).generate(), index)

    @staticmethod
    def from_edges(edges: List[Tuple[int, int]], index=""):
        n = max(max(u, v) for u, v in edges) + 1
        g = nk.graph.Graph(n)
        for u, v in edges:
            g.addEdge(u, v)
        return Graph(g, index)

    @staticmethod
    def from_straight_line(n: int, index=""):
        """A linked-list graph with n nodes"""
        return Graph.from_edges([(i, i + 1) for i in range(n - 1)], index)

    @staticmethod
    def from_clique(n: int, index=""):
        return Graph.from_edges(
            [(i, j) for i in range(n - 1) for j in range(i + 1, n)], index
        )

    def to_intangible(self, graph):
        return IntangibleSubgraph(list(self.nodes()), self.index)

    def to_igraph(self):
        import igraph as ig

        cont_ids = nk.graphtools.getContinuousNodeIds(self._data)
        compact_graph = nk.graphtools.getCompactedGraph(self._data, cont_ids)
        edges = [(u, v) for u, v in compact_graph.iterEdges()]
        return ig.Graph(self.n(), edges)


@dataclass
class IntangibleSubgraph:
    """A yet to be realized subgraph, containing only the node ids"""

    subset: List[int]
    index: str

    def realize(self, graph: Graph) -> Graph:
        """Realize the subgraph"""
        return graph.induced_subgraph(self.subset, self.index)

    def __len__(self):
        return len(self.subset)

    def n(self):
        return len(self)

    @staticmethod
    def from_assignment_pairs(
        pairs: Iterator[Tuple[int, str]]
    ) -> List[IntangibleSubgraph]:
        clusters: Dict[str, IntangibleSubgraph] = {}
        for node, cluster in pairs:
            if cluster not in clusters:
                clusters[cluster] = IntangibleSubgraph([], cluster)
            clusters[cluster].subset.append(node)
        res = list(v for v in clusters.values() if v.n() > 0)
        if not res:
            raise ValueError("No non-singleton clusters found. Aborting.")
        return res

    @cached_property
    def nodeset(self):
        return set(self.subset)

    def edges(self, graph: Graph) -> Iterator[Tuple[int, int]]:
        for n in self.subset:
            for e in graph._data.iterNeighbors(n):
                if e in self.nodeset:
                    yield n, e

    def nodes(self) -> Iterator[int]:
        return iter(self.subset)

    def count_edges(self, global_graph: Graph):
        return sum(1 for _ in self.edges(global_graph)) // 2

    def internal_degree(self, u, graph: Graph) -> int:
        return sum(1 for v in graph._data.iterNeighbors(u) if v in self.nodeset)

    def count_mcd(self, graph: Graph) -> int:
        if self.n() == 0:
            return 0
        return min(self.internal_degree(u, graph) for u in self.subset)

    def is_tree_like(self, global_graph: Graph) -> bool:
        m = self.count_edges(global_graph)
        n = self.n()
        return m == n - 1
