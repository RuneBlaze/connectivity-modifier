from dataclasses import dataclass

from hm01.types import AbstractCluterer


@dataclass
class LeidenClusterer(AbstractCluterer):
    resolution : float

    def cluster(self, graph):
        pass