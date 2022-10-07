from enum import Enum
import json
import re

import click
import networkit as nk
import numpy as np


class ColumnOrder(Enum):
    NODE_TO_CLUSTER_ID = (0, 1)
    CLUSTER_TO_NODE_ID = (1, 0)

def file_to_dict(clustering, column_order):
    cluster_to_id_dict = {}
    id_to_cluster_dict = {}

    with open(clustering, "r") as f:
        for current_line in f:
            current_line_arr = current_line.strip().split()
            current_node_id = int(current_line_arr[column_order.value[0]])
            current_cluster_id = str(current_line_arr[column_order.value[1]])

            if(current_cluster_id not in cluster_to_id_dict):
                cluster_to_id_dict[current_cluster_id] = []
            if(current_node_id not in id_to_cluster_dict):
                id_to_cluster_dict[current_node_id] = []

            cluster_to_id_dict[current_cluster_id].append(current_node_id)
            id_to_cluster_dict[current_node_id].append(current_cluster_id)

    return {
        "cluster_to_id_dict": cluster_to_id_dict,
        "id_to_cluster_dict": id_to_cluster_dict,
    }


def evaluate_single_cluster(graph, cluster_member_arr):
    int_cluster_member_arr = [int(node_id) for node_id in cluster_member_arr]
    boundary = 0
    volume = 0
    l_s = 0
    d_s = 0
    for node in int_cluster_member_arr:
        d_s += graph.degree(node)
    L = graph.numberOfEdges()

    current_min_k = None
    for cluster_member in int_cluster_member_arr:
        current_k = 0
        for neighbor in graph.iterNeighbors(cluster_member):
            if(neighbor not in int_cluster_member_arr):
                boundary += 1
            else:
                current_k += 1
                l_s += 1

        if(current_min_k is None):
            current_min_k = current_k
        current_min_k = min(current_min_k, current_k)

        volume += graph.degree(cluster_member)

    l_s /= 2
    assert current_min_k != 0
    equation_2 = (l_s / L) - ((d_s / (2 * L))**2)
    if(min(volume, 2 * L - volume) == 0):
        conductance = -42
    else:
        conductance = boundary / (min(volume, 2 * L - volume))
    return {
        "modularity": equation_2,
        "mcd": current_min_k,
        "conductance": conductance,
    }


def track_clusters_that_changed(initial_cluster_dicts, final_cluster_dicts):
    new_to_original_cluster_id_dict = {}
    new_clusters = final_cluster_dicts["cluster_to_id_dict"]
    for original_cluster_id in initial_cluster_dicts["cluster_to_id_dict"]:
        new_clusters.pop(original_cluster_id, None)

    for new_cluster_id in new_clusters:
        match_original_cluster_id = re.compile("[^\W\d]").search(new_cluster_id)
        original_cluster_id = new_cluster_id[:match_original_cluster_id.start()]
        new_to_original_cluster_id_dict[new_cluster_id] = original_cluster_id
    return new_to_original_cluster_id_dict

def track_marker_nodes_in_clusters_that_changed(new_to_original_cluster_id_dict, initial_cluster_dicts, final_cluster_dicts, marker_nodes_file):
    marker_nodes_coverage_dict = {}
    marker_nodes_set = set()
    with open(marker_nodes_file, "r") as f:
        next(f)
        for line in f:
            marker_nodes_set.add(int(line.strip().split(",")[1]))

    for new_cluster_id,original_cluster_id in new_to_original_cluster_id_dict.items():
        if(new_cluster_id not in marker_nodes_coverage_dict):
            marker_nodes_coverage_dict[new_cluster_id] = len(set(final_cluster_dicts["cluster_to_id_dict"][new_cluster_id]).intersection(marker_nodes_set))
        if(original_cluster_id not in marker_nodes_coverage_dict):
            marker_nodes_coverage_dict[original_cluster_id] = len(set(initial_cluster_dicts["cluster_to_id_dict"][original_cluster_id]).intersection(marker_nodes_set))
    return marker_nodes_coverage_dict

def track_cluster_stats(graph, new_to_original_cluster_id_dict, initial_cluster_dicts, final_cluster_dicts):
    cluster_info_dict = {}
    for new_cluster_id,original_cluster_id in new_to_original_cluster_id_dict.items():
        new_cluster_member_arr = final_cluster_dicts["cluster_to_id_dict"][new_cluster_id]
        original_cluster_member_arr = initial_cluster_dicts["cluster_to_id_dict"][original_cluster_id]
        if(new_cluster_id not in cluster_info_dict):
            cluster_info_dict[new_cluster_id] = evaluate_single_cluster(graph, new_cluster_member_arr)
        if(original_cluster_id not in cluster_info_dict):
            cluster_info_dict[original_cluster_id] = evaluate_single_cluster(graph, original_cluster_member_arr)
    return cluster_info_dict

@click.command()
@click.option("--initial-clustering", required=True, type=click.Path(exists=True), help="Input initial clustering")
@click.option("--final-clustering", required=True, type=click.Path(exists=True), help="Input final clustering")
@click.option("--input-network", required=True, type=click.Path(exists=True), help="Input network")
@click.option("--marker-nodes-file", required=True, type=click.Path(exists=True), help="Marker nodes file")
@click.option("--output-file", required=True, type=click.Path(), help="Output file")
def compare_clusterings(initial_clustering, final_clustering, input_network, marker_nodes_file, output_file):
    '''This is the main function that takes in two input clusterings in the format
    where initial clustering is "<cluster number>SPACE<node id>" and the final
    clustering is "<node id>SPACE<cluster number>". Input network should be a tab
    separated edge list with node ids corresponding to the input network where
    all the node ids are integers. The marker nodes file should be "doi,integer_id,pub_id"
    for each line in the file.
    The code outputs the following statistics.
    1.  Marker node coverage in non-singleton clusters that changed
    2.  Change in the number of non-singleton clusters
    3.  Change in the number of nodes in non-singleton clusters that changed
    4.  Change in the modularity in non-singleton clusters that changed
    5.  Change in the conductance in non-singleton clusters that changed
    6.  Total modularity score
    '''
    graph = nk.readGraph(input_network, nk.Format.EdgeListTabZero)
    initial_cluster_dicts = file_to_dict(initial_clustering, ColumnOrder.CLUSTER_TO_NODE_ID)
    initial_cluster_to_id_dict = initial_cluster_dicts["cluster_to_id_dict"]
    initial_id_to_cluster_dict = initial_cluster_dicts["id_to_cluster_dict"]
    final_cluster_dicts = file_to_dict(final_clustering, ColumnOrder.NODE_TO_CLUSTER_ID)
    final_cluster_to_id_dict = final_cluster_dicts["cluster_to_id_dict"]
    final_id_to_cluster_dict = final_cluster_dicts["id_to_cluster_dict"]

    new_to_original_cluster_id_dict = track_clusters_that_changed(initial_cluster_dicts, final_cluster_dicts)
    marker_nodes_coverage_dict = track_marker_nodes_in_clusters_that_changed(new_to_original_cluster_id_dict, initial_cluster_dicts, final_cluster_dicts, marker_nodes_file)
    cluster_info_dict = track_cluster_stats(graph, new_to_original_cluster_id_dict, initial_cluster_dicts, final_cluster_dicts)


    with open(output_file, "a+") as f:
        f.write(f"Mapping of old to new cluster ids:\n")
        for new_cluster_id,original_cluster_id in new_to_original_cluster_id_dict.items():
            f.write(f"{original_cluster_id} -> {new_cluster_id}\n")

    with open(output_file, "a+") as f:
        f.write(f"Mapping of old to new cluster ids with number of nodes:\n")
        for new_cluster_id,original_cluster_id in new_to_original_cluster_id_dict.items():
            f.write(f"{original_cluster_id}({len(initial_cluster_to_id_dict[original_cluster_id])}) -> {new_cluster_id}({len(final_cluster_to_id_dict[new_cluster_id])})\n")

    with open(output_file, "a+") as f:
        f.write(f"Mapping of old to new cluster ids with number of marker nodes:\n")
        for new_cluster_id,original_cluster_id in new_to_original_cluster_id_dict.items():
            f.write(f"{original_cluster_id}({marker_nodes_coverage_dict[original_cluster_id]}) -> {new_cluster_id}({marker_nodes_coverage_dict[new_cluster_id]})\n")

    with open(output_file, "a+") as f:
        f.write(f"Mapping of old to new cluster ids with modularity scores:\n")
        for new_cluster_id,original_cluster_id in new_to_original_cluster_id_dict.items():
            original_modularity = cluster_info_dict[original_cluster_id]["modularity"]
            new_modularity = cluster_info_dict[new_cluster_id]["modularity"]
            f.write(f"{original_cluster_id}({original_modularity}) -> {new_cluster_id}({new_modularity})\n")

    with open(output_file, "a+") as f:
        f.write(f"Mapping of old to new cluster ids with mcd scores:\n")
        for new_cluster_id,original_cluster_id in new_to_original_cluster_id_dict.items():
            original_mcd = cluster_info_dict[original_cluster_id]["mcd"]
            new_mcd = cluster_info_dict[new_cluster_id]["mcd"]
            f.write(f"{original_cluster_id}({original_mcd}) -> {new_cluster_id}({new_mcd})\n")

    with open(output_file, "a+") as f:
        f.write(f"Mapping of old to new cluster ids with conductance scores:\n")
        for new_cluster_id,original_cluster_id in new_to_original_cluster_id_dict.items():
            original_conductance = cluster_info_dict[original_cluster_id]["conductance"]
            new_conductance = cluster_info_dict[new_cluster_id]["conductance"]
            f.write(f"{original_cluster_id}({original_conductance}) -> {new_cluster_id}({new_conductance})\n")


    # evaluate_clustering(cluster_to_id_dict, id_to_cluster_dict, graph, figure_prefix, output_prefix)
    # evaluate_individual_clusters(cursor, table_name, cluster_to_id_dict, id_to_cluster_dict, graph, output_prefix)
    # track_nodes(nodes_of_interest, cluster_to_id_dict, id_to_cluster_dict, output_prefix)


if __name__ == "__main__":
    compare_clusterings()
