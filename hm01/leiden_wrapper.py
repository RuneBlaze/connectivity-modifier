from dataclasses import dataclass


@dataclass
class LeidenClusterer:
    resolution : float

    def cluster(self, graph):
        pass