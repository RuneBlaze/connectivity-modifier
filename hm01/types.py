from abc import abstractmethod
from typing import Iterator, List, Protocol

from hm01.basics import IntangibleSubgraph

class AbstractCluterer(Protocol):
    @abstractmethod
    def cluster(self, graph) -> Iterator[IntangibleSubgraph]:
        raise NotImplementedError

    def cluster_without_singletons(self, graph) -> Iterator[IntangibleSubgraph]:
        for cluster in self.cluster(graph):
            if cluster.n() > 1:
                yield cluster
    
    @abstractmethod
    def from_existing_clustering(self, filepath) -> List[IntangibleSubgraph]:
        raise NotImplementedError