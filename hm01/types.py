from typing import Iterator, Protocol

from hm01.basics import IntangibleSubgraph

class AbstractCluterer(Protocol):
    def cluster(self, graph) -> Iterator[IntangibleSubgraph]:
        pass