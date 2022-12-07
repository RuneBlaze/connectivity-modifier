from __future__ import annotations
from dataclasses import dataclass
import typer
from enum import Enum
from typing import List, Optional, Tuple, Union, Dict, Deque
import math
import time
from collections import deque
from hm01.basics import Graph, IntangibleSubgraph
from hm01.leiden_wrapper import LeidenClusterer, Quality
from itertools import chain
import treeswift as ts
import networkit as nk
from structlog import get_logger
import jsonpickle
from hm01.types import AbstractClusterer
from .ikc_wrapper import IkcClusterer
from .context import context
from .connectivity_requirement import MincutRequirement
from .pruner import prune_graph


class ClustererSpec(str, Enum):
    leiden = "leiden"
    ikc = "ikc"
    leiden_mod = "leiden_mod"


def summarize_graphs(graphs: List[IntangibleSubgraph]) -> str:
    if not graphs:
        return "[](empty)"
    if len(graphs) > 3:
        return f"[{graphs[0].index}, ..., {graphs[-1].index}]({len(graphs)})"
    else:
        return f"[{', '.join([g.index for g in graphs])}]({len(graphs)})"


def annotate_tree_node(node: ts.Node, graph: Union[Graph, IntangibleSubgraph]):
    node.label = graph.index
    node.graph_index = graph.index
    node.num_nodes = graph.n()
    node.extant = False


@dataclass
class ClusterIgnoreFilter:
    ignore_trees: bool
    ignore_smaller_than: int

    def __call__(self, cluster: IntangibleSubgraph, global_graph: Graph) -> bool:
        if self.ignore_trees and cluster.is_tree_like(global_graph) == 1:
            return True
        if self.ignore_smaller_than > 0 and cluster.n() < self.ignore_smaller_than:
            return True
        return False

    @staticmethod
    def default() -> ClusterIgnoreFilter:
        return ClusterIgnoreFilter(False, 0)


def algorithm_g(
    global_graph: Graph,
    graphs: List[IntangibleSubgraph],
    clusterer: Union[IkcClusterer, LeidenClusterer],
    requirement: MincutRequirement,
    filterer: ClusterIgnoreFilter = ClusterIgnoreFilter.default(),
) -> Tuple[List[IntangibleSubgraph], Dict[int, str], ts.Tree]:
    log = get_logger()
    tree = ts.Tree()
    annotate_tree_node(tree.root, global_graph)
    node_mapping: Dict[str, ts.Node] = {}
    for g in graphs:
        n = ts.Node()
        annotate_tree_node(n, g)
        tree.root.add_child(n)
        node_mapping[g.index] = n
    queue: Deque[IntangibleSubgraph] = deque(graphs)
    log.info("starting algorithm-g", queue_size=len(queue))
    ans: List[IntangibleSubgraph] = []
    node2cids = {}
    while queue:
        log = get_logger()
        log.debug("entered next iteration of loop", queue_size=len(queue))
        intangible_graph = queue.popleft()
        log.debug(
            "popped graph",
            graph_n=intangible_graph.n(),
            graph_index=intangible_graph.index,
        )
        if intangible_graph.n() <= 1:
            continue
        if filterer(intangible_graph, global_graph):
            log.debug("filtered graph", graph_index=intangible_graph.index)
            ans.append(intangible_graph)
            continue
        graph = intangible_graph.realize(global_graph)
        tree_node = node_mapping[graph.index]
        log = log.bind(
            g_id=graph.index, g_n=graph.n(), g_m=graph.m(), g_mcd=graph.mcd()
        )
        num_pruned = prune_graph(graph, requirement, clusterer)
        if num_pruned > 0:
            log = log.bind(
                g_id=graph.index, g_n=graph.n(), g_m=graph.m(), g_mcd=graph.mcd()
            )
            log.info("pruned graph", num_pruned=num_pruned)
            new_child = ts.Node()
            graph.index = f"{graph.index}δ"
            annotate_tree_node(new_child, graph)
            tree_node.add_child(new_child)
            node_mapping[graph.index] = new_child
            tree_node = new_child
        for n in graph.nodes():
            node2cids[n] = graph.index
        mincut_res = graph.find_mincut()
        # is a cluster "cut-valid" -- having good connectivity?
        valid_threshold = requirement.validity_threshold(clusterer, graph)
        log.debug("calculated validity threshold", validity_threshold=valid_threshold)
        log.debug(
            "mincut computed",
            a_side_size=len(mincut_res.light_partition),
            b_side_size=len(mincut_res.heavy_partition),
            cut_size=mincut_res.cut_size,
        )
        tree_node.cut_size = mincut_res.cut_size
        tree_node.validity_threshold = valid_threshold
        if mincut_res.cut_size <= valid_threshold and mincut_res.cut_size > 0:
            p1, p2 = graph.cut_by_mincut(mincut_res)
            node_a = ts.Node()
            node_b = ts.Node()
            annotate_tree_node(node_a, p1)
            annotate_tree_node(node_b, p2)
            tree_node.add_child(node_a)
            tree_node.add_child(node_b)
            node_mapping[p1.index] = node_a
            node_mapping[p2.index] = node_b
            subp1 = list(clusterer.cluster_without_singletons(p1))
            subp2 = list(clusterer.cluster_without_singletons(p2))
            for p, np in [(subp1, node_a), (subp2, node_b)]:
                for sg in p:
                    n = ts.Node()
                    annotate_tree_node(n, sg)
                    node_mapping[sg.index] = n
                    np.add_child(n)
            queue.extend(subp1)
            queue.extend(subp2)
            log.info(
                "cluster split",
                num_a_side=len(subp1),
                num_b_side=len(subp2),
                summary_a_side=summarize_graphs(subp1),
                summary_b_side=summarize_graphs(subp2),
            )
        else:
            candidate = graph.to_intangible(global_graph)
            mod = global_graph.modularity_of(candidate)
            # TODO: stop ad-hoc checks of the clusterer being IkcClusterer and
            # and thus need to use the modularity of the candidate
            if not isinstance(clusterer, IkcClusterer) or mod > 0:
                ans.append(candidate)
                node_mapping[graph.index].extant = True
                log.info("cut valid, not splitting anymore")
            else:
                node_mapping[graph.index].extant = False
                log.info(
                    "cut valid, but modularity non-positive, thrown away",
                    modularity=mod,
                )
        del graph.data
    return ans, node2cids, tree


def main(
    input: str = typer.Option(..., "--input", "-i"),
    working_dir: Optional[str] = typer.Option("", "--working-dir", "-d"),
    clusterer_spec: ClustererSpec = typer.Option(..., "--clusterer", "-c"),
    existing_clustering: Optional[str] = typer.Option(
        "", "--existing-clustering", "-e"
    ),
    k: int = typer.Option(-1, "--k", "-k"),
    resolution: float = typer.Option(-1, "--resolution", "-g"),
    threshold: str = typer.Option("", "--threshold", "-t"),
    output: str = typer.Option("", "--output", "-o"),
    ignore_trees: bool = typer.Option(False, "--ignore-trees", "-x"),
    ignore_smaller_than: int = typer.Option(0, "--ignore-smaller-than", "-s"),
):
    """Connectivity-Modifier (CM). Take a network and cluster it ensuring cut validity"""
    if clusterer_spec == ClustererSpec.leiden:
        assert resolution != -1
        clusterer: Union[LeidenClusterer, IkcClusterer] = LeidenClusterer(resolution)
    elif clusterer_spec == ClustererSpec.leiden_mod:
        assert resolution == -1, "Leiden with modularity does not support resolution"
        clusterer = LeidenClusterer(resolution, quality=Quality.modularity)
    else:
        assert k != -1
        clusterer = IkcClusterer(k)
    log = get_logger()
    context.with_working_dir(input + "_working_dir" if not working_dir else working_dir)
    log.info(
        f"starting hm01",
        input=input,
        working_dir=context.working_dir,
        clusterer=clusterer,
    )
    requirement = MincutRequirement.try_from_str(threshold)
    log.info(f"parsed connectivity requirement", requirement=requirement)
    filterer = ClusterIgnoreFilter(ignore_trees, ignore_smaller_than)
    log.info(f"parsed cluster filter", filterer=filterer)
    time1 = time.time()
    edgelist_reader = nk.graphio.EdgeListReader("\t", 0)
    nk_graph = edgelist_reader.read(input)
    log.info(
        f"loaded graph",
        n=nk_graph.numberOfNodes(),
        m=nk_graph.numberOfEdges(),
        elapsed=time.time() - time1,
    )
    root_graph = Graph(nk_graph, "")
    if not existing_clustering:
        log.info(
            f"running first round of clustering before algorithm-g", clusterer=clusterer
        )
        clusters = list(clusterer.cluster_without_singletons(root_graph))
    else:
        log.info(f"loading existing clustering before algorithm-g", clusterer=clusterer)
        clusters = clusterer.from_existing_clustering(existing_clustering)
    log.info(
        f"first round of clustering obtained",
        num_clusters=len(clusters),
        summary=summarize_graphs(clusters),
    )
    new_clusters, labels, tree = algorithm_g(
        root_graph, clusters, clusterer, requirement, filterer
    )
    with open(output, "w+") as f:
        for n, cid in labels.items():
            f.write(f"{n} {cid}\n")
    with open(output + ".tree.json", "w+") as f:
        f.write(jsonpickle.encode(tree))


def entry_point():
    typer.run(main)


if __name__ == "__main__":
    entry_point()
