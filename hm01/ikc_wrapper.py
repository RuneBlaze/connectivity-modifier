from dataclasses import dataclass
from config import Config

@dataclass
class IkcClusterer:
    k : int

    def cluster(self, graph):
        """Returns a list of (labeled) subgraphs on the graph"""
        pass