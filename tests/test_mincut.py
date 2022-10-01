from hm01.mincut import run_viecut_command
from hm01.basics import Graph
import networkit as nk
GRAPH_RESULTS = [
    ("data/ring_four_k10s.edge_list", nk.Format.EdgeListSpaceZero, (20, 20, 2)),
    ("data/two_k5s.edge_list", nk.Format.EdgeListTabZero, (0, 0, 0)),
]

def test_viecut_command(context):
    for i, (graph_path, fmt, (light_size, heavy_size, cut_size)) in enumerate(GRAPH_RESULTS):
        metis_filepath = Graph(nk.graphio.readGraph(graph_path, fmt), str(i)).as_metis_filepath()
        output_filepath = metis_filepath + ".cut"
        res = run_viecut_command(metis_filepath, output_filepath)
        assert res.cut_size == cut_size
        assert len(res.light_partition) == light_size
        assert len(res.heavy_partition) == heavy_size

def test_cut_api(context):
    for i, (graph_path, fmt, (light_size, heavy_size, cut_size)) in enumerate(GRAPH_RESULTS):
        graph = Graph(nk.graphio.readGraph(graph_path, fmt), str(i))
        res = graph.find_mincut()
        assert res.cut_size == cut_size
        assert len(res.light_partition) == light_size
        assert len(res.heavy_partition) == heavy_size