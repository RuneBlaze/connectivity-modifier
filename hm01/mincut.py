from dataclasses import dataclass
from typing import List, Tuple
from .context import context
import subprocess
import re
import os

@dataclass
class MincutResult:
    light_partition : List[int] # 0 labeled nodes
    heavy_partition : List[int] # 1 labeled nodes
    cut_size : int

    def realize(self, graph):
        """Realize the mincut result as a pair of graphs"""
        pass

def viecut(graph):
    metis = graph.as_metis_filepath()
    cut_path = metis + ".cut"
    cut_result = run_viecut_command(metis, cut_path, hydrator=graph.hydrator)
    return cut_result

def run_viecut_command(metis_path, output_path, hydrator=None):
    """Run the viecut command and return the output path"""
    res = subprocess.run([context.viecut_path, "-b", "-s", "-o", output_path, metis_path, "cactus"], capture_output=True)
    labels = []
    if not os.path.exists(output_path):
        return MincutResult([], [], 0)
    with open(output_path, "r") as f:
        for l in f:
            labels.append(int(l))
    light_partition = []
    heavy_partition = []
    for i, l in enumerate(labels):
        if l == 0:
            light_partition.append(i)
        else:
            heavy_partition.append(i)
    lastline = res.stdout.splitlines()[-1]
    cut_size = int(re.search(r"cut=(\d+)", lastline.decode("utf-8")).group(1))
    if hydrator:
        return MincutResult([hydrator[i] for i in light_partition], [hydrator[i] for i in heavy_partition], cut_size)
    else:
        return MincutResult(light_partition, heavy_partition, cut_size)