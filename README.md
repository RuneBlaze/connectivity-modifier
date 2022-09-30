## Setup

```bash
# poetry is a wrapper over virtual environments
peotry install # install networkit and co
peotry run pytest # run tests
peotry run python3 file_path.py # run a file
```


## Algorithm
```
f : Graph -> List[Cluster]
# f : Graph -> List[Graph (labeled)]
```

```python

s - a - rest_of_community
s, a - rest_of_community

g : Graph -> List[Cluster]
def g(graph):
    ans = []
    clusters = f(graph)
    for c in clusters:
        subgraph = graph.subgraph(c)
        cut_info = subgraph.cut() # VieCut
        if cut_info.is_bad(): # connectivity <= parameter
            subgraph1, subgraph2 = cut_info.cut_graph(subgraph)
            ans.extend(g(subgraph1))
            ans.extend(g(subgraph2))
        else:
            ans.append(c)
    return ans
```

## Id scheme for each cluster

0 .. n clusters
1a 1b
1a0 1a1 1a2

5a6b2

## The formats we need for third-party software
Input formats
- edgelist (with continuous ids) # Leiden and IKC
- metis (with continuous ids) # Viecut

Output formats
 - CSV from IKC
 - Leiden output (node_id cluster_id)
 - Viecut (standard output, and also the binary labels list)

```
1a3b6.metis
```

## Our output format

node_id cluster_id (the most specific cluster a node belongs to)

```
1 2
```