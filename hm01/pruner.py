from __future__ import annotations

from hm01.connectivity_requirement import MincutRequirement
from hm01.types import AbstractClusterer
from .basics import Graph
from heapdict import heapdict


def prune_graph(
    graph: Graph,
    connectivity_requirement: MincutRequirement,
    clusterer: AbstractClusterer,
) -> int:
    mcd = graph.mcd()
    if mcd > connectivity_requirement.validity_threshold(clusterer, graph):
        return 0
    deleted_nodes = 0
    degrees = heapdict()
    for node in graph.nodes():
        degrees[node] = graph.data.degree(node)
    while degrees:
        node, degree = degrees.popitem()
        if degree > connectivity_requirement.validity_threshold(
            clusterer, graph, mcd_override=degree
        ):
            break
        for neighbor in graph.data.iterNeighbors(node):
            degrees[neighbor] -= 1
        graph.data.removeNode(node)
        deleted_nodes += 1
    graph.mcd.cache_clear()
    return deleted_nodes
