from __future__ import annotations
from dataclasses import dataclass
import typer
from enum import Enum
from typing import List, Optional, Tuple, Union, Dict, Deque
import math
import time
from collections import deque
from hm01.basics import Graph, IntangibleSubgraph
from hm01.leiden_wrapper import LeidenClusterer
from itertools import chain
import treeswift as ts
import networkit as nk
from structlog import get_logger
import jsonpickle
from hm01.types import AbstractCluterer
from .ikc_wrapper import IkcClusterer
from .context import context

class ClustererSpec(str, Enum):
    leiden = "leiden"
    ikc = "ikc"


@dataclass
class MincutRequirement:
    """A linear combination of the log10 cluster size, mcd of the cluster, and the k given in the input"""

    log10: float
    mcd: float
    k: float
    constant: int

    def is_sane(self, clusterer):
        if self.log10 <= 0 and self.mcd <= 0 and self.k <= 0 and self.constant <= 0:
            return False
        if not isinstance(clusterer, IkcClusterer):
            return self.k == 0
        return True

    def validity_threshold(self, clusterer, cluster):
        log10 = math.log10(cluster.n())
        mcd = cluster.mcd()
        k = clusterer.k if isinstance(clusterer, IkcClusterer) else 0
        return self.log10 * log10 + self.mcd * mcd + self.k * k + self.constant

    @staticmethod
    def most_stringent() -> MincutRequirement:
        return MincutRequirement(0, 0, 0, 2)

    @staticmethod
    def try_from_str(s):
        """Parse a mincut requirement from a string (given in the CLI)"""
        s = s.replace(" ", "")

        def take_num(st):
            i = 0
            buf = []
            if not st or not st[i].isdigit():
                raise ValueError(f"Expected a number, got {st[i]}")
            while i < len(st) and (st[i].isdigit() or st[i] == "."):
                buf.append(st[i])
                i += 1
            return float("".join(buf)), st[i:]

        def one_of(words, s):
            for word in words:
                if s.startswith(word):
                    return word, s[len(word) :]
            raise ValueError(f"Expected one of {words}, got {s}")

        log10 = 0
        mcd = 0
        k = 0
        constant = 0
        vals = {}
        while s:
            n, s = take_num(s)
            if s and s[0] == "+":
                constant += n
                s = s[1:]
                continue
            if not s:
                constant += n
                break
            key, s = one_of(["log10", "mcd", "k"], s)
            vals[key] = float(n)
            if s and s[0] == "+":
                s = s[1:]
        if "log10" in vals:
            log10 = vals["log10"]
        if "mcd" in vals:
            mcd = vals["mcd"]
        if "k" in vals:
            k = vals["k"]
        return MincutRequirement(log10, mcd, k, constant)


def summarize_graphs(graphs: List[IntangibleSubgraph]) -> str:
    if not graphs:
        return "[](empty)"
    if len(graphs) > 3:
        return f"[{graphs[0].index}, ..., {graphs[-1].index}]({len(graphs)})"
    else:
        return f"[{', '.join([g.index for g in graphs])}]({len(graphs)})"


def annotate_tree_node(node : ts.Node, graph : Union[Graph, IntangibleSubgraph]):
    node.label = graph.index
    node.graph_index = graph.index
    node.num_nodes = graph.n()
    node.extant = False

def algorithm_g(
    global_graph: Graph,
    graphs: List[IntangibleSubgraph],
    clusterer: Union[IkcClusterer, LeidenClusterer],
    requirement: MincutRequirement,
) -> Tuple[List[IntangibleSubgraph], Dict[int, str], ts.Tree]:
    log = get_logger()
    tree = ts.Tree()
    annotate_tree_node(tree.root, global_graph)
    node_mapping : Dict[str, ts.Node] = {}
    for g in graphs:
        n = ts.Node()
        annotate_tree_node(n, g)
        tree.root.add_child(n)
        node_mapping[g.index] = n
    queue: Deque[IntangibleSubgraph] = deque(graphs)
    log.info("starting algorithm-g", queue_size=len(queue))
    ans = []
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
        graph = intangible_graph.realize(global_graph)
        tree_node = node_mapping[graph.index]
        log = log.bind(g_id=graph.index, g_n=graph.n(), g_m=graph.m(), g_mcd=graph.mcd())
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
            ans.append(graph.to_intangible(global_graph))
            node_mapping[graph.index].extant = True
            log.info("cut valid, not splitting anymore")
        del graph.data
    return ans, node2cids, tree


def main(
    input: str = typer.Option(..., "--input", "-i"),
    working_dir: Optional[str] = typer.Option("", "--working-dir", "-d"),
    clusterer_spec: ClustererSpec = typer.Option(..., "--clusterer", "-c"),
    k: int = typer.Option(-1, "--k", "-k"),
    resolution: float = typer.Option(-1, "--resolution", "-g"),
    threshold: str = typer.Option("", "--threshold", "-t"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
):
    """Take a network and cluster it ensuring cut validity"""
    if clusterer_spec == ClustererSpec.leiden:
        assert resolution != -1
        clusterer: Union[LeidenClusterer, IkcClusterer] = LeidenClusterer(resolution)
    else:
        assert k != -1
        clusterer = IkcClusterer(k)
    log = get_logger()
    context.with_working_dir(input + "_working_dir" if not working_dir else working_dir)
    log.info(f"loaded graph", input=input, working_dir=context.working_dir)
    requirement = MincutRequirement.try_from_str(threshold)
    log.info(f"parsed connectivity requirement", requirement=requirement)
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
    log.info(
        f"running first round of clustering before algorithm-g", clusterer=clusterer
    )
    clusters = list(clusterer.cluster_without_singletons(root_graph))
    log.info(
        f"first round of clustering done",
        num_clusters=len(clusters),
        summary=summarize_graphs(clusters),
    )
    new_clusters, labels, tree = algorithm_g(root_graph, clusters, clusterer, requirement)
    if output:
        with open(output, "w") as f:
            for n, cid in labels.items():
                f.write(f"{n} {cid}\n")
        with open(output + ".tree.json", "w+") as f:
            f.write(jsonpickle.encode(tree))
    else:
        for n, cid in labels.items():
            print(f"{n} {cid}")

def entry_point():
    typer.run(main)

if __name__ == "__main__":
    entry_point()
