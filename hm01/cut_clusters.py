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
import coloredlogs, logging
import networkit as nk

from hm01.types import AbstractCluterer
from .ikc_wrapper import IkcClusterer
from .context import context

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
coloredlogs.install(level="DEBUG", logger=logger)

class ClustererSpec(str, Enum):
    leiden = "leiden"
    ikc = "ikc"

@dataclass
class MincutRequirement:
    """A linear combination of the log10 cluster size, mcd of the cluster, and the k given in the input"""
    log10: float
    mcd: float
    k: float
    constant : int

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
        return self.log10 * log10 + self.mcd * mcd + self.k * k

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
            if s and s[0] == '+':
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

def summarize_graphs(graphs : List[IntangibleSubgraph]) -> str:
    if not graphs:
        return "[](empty)"
    if len(graphs) > 3:
        return f"[{graphs[0].index}, ..., {graphs[-1].index}]({len(graphs)})"
    else:
        return f"[{', '.join([g.index for g in graphs])}]({len(graphs)})"

def algorithm_g(
    global_graph: Graph,
    graphs: List[IntangibleSubgraph],
    clusterer: Union[IkcClusterer, LeidenClusterer],
    requirement: MincutRequirement,
) -> Tuple[List[IntangibleSubgraph], Dict[int, str]]:
    logger.info("Starting algorithm-g")
    queue : Deque[IntangibleSubgraph] = deque(graphs)
    logger.info("Initially having %d subgraphs", len(queue))
    ans = []
    node2cids = {}
    while queue:
        graph = queue.popleft().realize(global_graph)
        for n in graph.nodes():
            node2cids[n] = graph.index
        if graph.n() <= 1:
            ans.append(graph.to_intangible(global_graph))
            continue
        mincut_res = graph.find_mincut()
        # is a cluster "cut-valid" -- having good connectivity?
        valid_threshold = requirement.validity_threshold(clusterer, graph)
        logger.debug("Valid threshold (ID=%s): %f", graph.index, valid_threshold)
        logger.debug("Mincut result (ID=%s): light side=%d heavy side=%d cut size=%d", graph.index, len(mincut_res.light_partition), len(mincut_res.heavy_partition), mincut_res.cut_size)
        if mincut_res.cut_size <= valid_threshold:
            p1, p2 = graph.cut_by_mincut(mincut_res)
            subp1 = list(clusterer.cluster(p1))
            subp2 = list(clusterer.cluster(p2))
            queue.extend(subp1)
            queue.extend(subp2)
            logger.info("Clusters split (ID=%s): into %s and %s", graph.index, summarize_graphs(subp1), summarize_graphs(subp2))
        else:
            ans.append(graph.to_intangible(global_graph))
            logger.info("Cut-valid, not splitting anymore (ID=%s)", graph.index)
        del graph.data
    return ans, node2cids


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
        clusterer : Union[LeidenClusterer, IkcClusterer] = LeidenClusterer(resolution)
    else:
        assert k != -1
        clusterer = IkcClusterer(k)
    context.with_working_dir(input + "_working_dir" if not working_dir else working_dir)
    logger.info(f"Loading graph from {input} with working directory {context.working_dir}")
    requirement = MincutRequirement.try_from_str(threshold)
    logger.info(f"Connectivity requirement: {requirement}")
    time1 = time.time()
    edgelist_reader = nk.graphio.EdgeListReader('\t',0)
    nk_graph = edgelist_reader.read(input)
    logger.info(f"Loaded graph with {nk_graph.numberOfNodes()} nodes and {nk_graph.numberOfEdges()} edges in {time.time() - time1:.2f} seconds")
    root_graph = Graph(nk_graph, "")
    logger.info(f"Running first round of clustering before handing to algorithm-g")
    clusters = list(root_graph.find_clusters(clusterer))
    new_clusters, labels = algorithm_g(root_graph, clusters, clusterer, requirement)
    if output:
        with open(output, "w") as f:
            for n, cid in labels.items():
                f.write(f"{n} {cid}\n")
    else:
        for n, cid in labels.items():
            print(f"{n} {cid}")

def entry_point():
    typer.run(main)

if __name__ == "__main__":
    entry_point()
