from dataclasses import dataclass
from typing import List, Tuple

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