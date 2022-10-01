from __future__ import annotations
from dataclasses import dataclass
import typer
from enum import Enum
from typing import List, Optional, Tuple, Union, Dict
import math
from collections import deque
from hm01.basics import Graph
from hm01.leiden_wrapper import LeidenClusterer
import networkit as nk
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
    constant : int

    def is_sane(self, clusterer):
        if self.log10 <= 0 and self.mcd <= 0 and self.k <= 0 and self.constant <= 0:
            return False
        if not isinstance(clusterer, IkcClusterer):
            return self.k == 0
        return True

    def decide_validity(self, clusterer, cluster, mincut_res):
        log10 = math.log10(cluster.n())
        mcd = cluster.mcd()
        k = clusterer.k if isinstance(clusterer, IkcClusterer) else 0
        return self.log10 * log10 + self.mcd * mcd + self.k * k >= mincut_res.cut_size

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

def algorithm_g(
    graphs: List[Graph],
    clusterer: Union[IkcClusterer, LeidenClusterer],
    requirement: MincutRequirement,
) -> Tuple[List[Graph], Dict[int, str]]:
    queue = deque(graphs)
    ans = []
    node2cids = {}
    while queue:
        graph = queue.popleft()
        for n in graph.nodes():
            node2cids[n] = graph.index
        if graph.n() <= 1:
            ans.append(graph)
            continue
        mincut_res = graph.find_mincut()
        # is a cluster "cut-valid" -- having good connectivity?
        is_cut_valid = requirement.decide_validity(clusterer, graph, mincut_res)
        if not is_cut_valid:
            p1, p2 = graph.cut_by_mincut(mincut_res)
            queue.append(p1)
            queue.append(p2)
        else:
            ans.append(graph)
    return ans, node2cids


def main(
    input: str = typer.Option(..., "--input", "-i"),
    clusterer: ClustererSpec = typer.Option(..., "--clusterer", "-c"),
    k: int = typer.Option(-1, "--k", "-k"),
    resolution: float = typer.Option(-1, "--resolution", "-g"),
    threshold: str = typer.Option("", "--threshold", "-t"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
):
    if clusterer == ClustererSpec.leiden:
        assert resolution != -1
        clusterer = LeidenClusterer(resolution)
    else:
        assert k != -1
        clusterer = IkcClusterer(k)
    context.with_working_dir(input + "_working_dir")
    requirement = MincutRequirement.try_from_str(threshold)
    edgelist_reader = nk.graphio.EdgeListReader('\t',0)
    nk_graph = edgelist_reader.read(input)
    root_graph = Graph(nk_graph, "")
    clusters = clusterer.cluster(root_graph)
    new_clusters, labels = algorithm_g(clusters, clusterer, requirement)
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
