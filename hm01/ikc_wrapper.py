from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import List, Iterator, Dict, Optional, Tuple, Union
from collections import defaultdict
import csv

import networkit as nk

from hm01.types import AbstractClusterer

from .basics import Graph, IntangibleSubgraph
from .context import context


@dataclass
class IkcClusterer(AbstractClusterer):
    k: int

    def cluster(self, graph) -> Iterator[IntangibleSubgraph]:
        """Returns a list of (labeled) subgraphs on the graph"""
        # retarr = []
        output_prefix = context.request_graph_related_path(graph, "ikc")
        Path(output_prefix).mkdir(
            exist_ok=True
        )  # should create a directory like "IKC_working_directory)

        global_name_networkit_graph = (
            graph.data
        )  # the networkit graph with non-translated node ids
        cluster_id = graph.index  # the cluster id such as 5a6b2

        old_to_new_node_id_mapping = nk.graphtools.getContinuousNodeIds(
            global_name_networkit_graph
        )
        new_to_old_node_id_mapping = {
            new_id: old_id for old_id, new_id in old_to_new_node_id_mapping.items()
        }
        local_name_networkit_graph = nk.graphtools.getCompactedGraph(
            global_name_networkit_graph, old_to_new_node_id_mapping
        )
        local_name_networkit_graph_filename = (
            f"{output_prefix}/{cluster_id}.local_mapping.edge_list"
        )
        nk.writeGraph(
            local_name_networkit_graph,
            local_name_networkit_graph_filename,
            nk.Format.EdgeListTabZero,
        )

        raw_ikc_clustering_output_filename = (
            f"{output_prefix}/{cluster_id}.ikc_clusterting.raw"
        )
        self.run_ikc(
            local_name_networkit_graph_filename,
            cluster_id,
            output_prefix,
            raw_ikc_clustering_output_filename,
        )

        ikc_clustering_output_filename = f"{output_prefix}/{cluster_id}.ikc_clusterting"
        self.parse_ikc_output(
            raw_ikc_clustering_output_filename, ikc_clustering_output_filename
        )
        clustering_mappings = self.ikc_output_to_dict(ikc_clustering_output_filename)
        cluster_to_id_dict = clustering_mappings["cluster_to_id_dict"]
        id_to_cluster_dict = clustering_mappings["id_to_cluster_dict"]

        for local_cluster_id, local_cluster_member_arr in cluster_to_id_dict.items():
            global_cluster_id = f"{cluster_id}{local_cluster_id}"
            global_cluster_member_arr = [
                int(new_to_old_node_id_mapping[local_id])
                for local_id in local_cluster_member_arr
            ]
            yield graph.intangible_subgraph(
                global_cluster_member_arr, str(local_cluster_id)
            )
        # return retarr

    def run_ikc(self, edge_list_path, cluster_id, output_prefix, output_file):
        """Runs IKC given an edge list and writes a CSV"""
        ikc_path = context.ikc_path
        with open(f"{output_prefix}/{cluster_id}_ikc_k={self.k}.stderr", "w") as f_err:
            with open(
                f"{output_prefix}/{cluster_id}_ikc_k={self.k}.stdout", "w"
            ) as f_out:
                subprocess.run(
                    [
                        "/usr/bin/time",
                        "-v",
                        "/usr/bin/env",
                        "python3",
                        ikc_path,
                        "-e",
                        edge_list_path,
                        "-o",
                        output_file,
                        "-k",
                        str(self.k),
                    ]
                )

    def parse_ikc_output(self, raw_clustering_output, clustering_output):
        with open(raw_clustering_output, "r") as f_raw:
            with open(clustering_output, "w") as f:
                for line in f_raw:
                    [node_id, cluster_number, k, modularity] = line.strip().split(",")
                    f.write(f"{cluster_number} {node_id}\n")

    def ikc_output_to_dict(self, clustering_output):
        cluster_to_id_dict = {}
        id_to_cluster_dict = {}
        with open(clustering_output, "r") as f:
            for line in f:
                [current_cluster_number, node_id] = line.strip().split()
                if int(current_cluster_number) not in cluster_to_id_dict:
                    cluster_to_id_dict[int(current_cluster_number)] = []
                if node_id not in id_to_cluster_dict:
                    id_to_cluster_dict[int(node_id)] = []
                cluster_to_id_dict[int(current_cluster_number)].append(int(node_id))
                id_to_cluster_dict[int(node_id)].append(int(current_cluster_number))

        return {
            "cluster_to_id_dict": cluster_to_id_dict,
            "id_to_cluster_dict": id_to_cluster_dict,
        }

    def from_existing_clustering(self, filepath) -> List[IntangibleSubgraph]:
        clusters = {}
        with open(filepath, newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            for row in reader:
                node_id = int(row[0])
                cluster_id = row[1]
                if cluster_id not in clusters:
                    clusters[cluster_id] = IntangibleSubgraph([], cluster_id)
                clusters[cluster_id].nodes.append(node_id)
        return list(clusters.values())
