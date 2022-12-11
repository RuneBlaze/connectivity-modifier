# cm

Connectivity Modifier (CM) is a generic meta-method for community detection while ensuring a certain connectivity
(global minimum cut size) bound on the output communities (clusters). To be more precise, suppose that you want
to ensure that Leiden clusters must not be "easily-cut", for example, the minimum cut size $\lambda$ must
be at least $\log_{10}(n)$, $n$ the size of any cluster, you can run CM paired with Leiden, and it will
ensure that all output clusters have that minimum size cut.

## Installation

Our software is provided via PyPI and supports at least Python 3.7.

```
pip3 install --pre connectivity-modifier # install prerelease version
```

Note that you must install [Viecut](https://github.com/VieCut/VieCut) as a dependency explicitly, i.e., `viecut` the binary must be compiled and the path to `viecut` must be specified in the config file (explained below).

Say that you installed `viecut` in `/foo/bar/viecut`, then you want to create a config file in `~/.config/cm/config.toml` and have something like this:

```toml
[tools]
ikc_path = "{project_root}/third_party/ikc.py" # {project_root} is a specific path resolving to the source code root
leiden_path = "" # currently obsolete
viecut_path = "/foo/bar/viecut" # viecut's path
```

Or if the main executable detects that `cm.toml` is in the current working directory, the `cm.toml` config file will have the highest priority instead.

After all this, try `cm --help`, and you should see something like this:

```bash
Usage: cm [OPTIONS]

  Connectivity-Modifier (CM). Take a network and cluster it ensuring cut
  validity

Options:
  -i, --input TEXT                [required]
[...]
```

## Usage

Our main executable is provided as `cm`, and we list the options below:

### `-i, --input GRAPH_TSV`

The input graph to be clustered, where `graph.tsv` is a tab-delimited edgelist, only including integer edge ids. Note that we follow the `igraph` convention, where we assume that the input node ids are continuous, and if not, dummy nodes are added.

### `-c, --clusterer [leiden|ikc|leiden_mod]`

The clusterer to be paired with. If using with an existing clustering (`-e`), then the same clusterer must be used (see below). Otherwise, one must decide which clusterer should be used. The clusterers are:

 - `leiden`: Leiden (`leidenalg`) with CPM optimization, must specify `-g, --resolution` later
 - `ikc`: Iterative k-core, must specify `-k` later
 - `leiden_mod`: Leiden with modularity optimization, no other parameters allowed to be specified

### -e, --existing-clustering CLUSTERING_FILE

Specifies the starting clustering (in effect saving time for `cm` to reproduce the initial clustering) to be `modified` to have sufficient connectivity thresholds (c.f. `-t`). The file format is "native" to the clustering method. For example, for IKC, it is the default IKC csv output format. For Leiden, it is the Leiden output format (i.e., tab-delimited node_id cluster_id file).

### `-g, --resolution FLOAT`, `-k, --k INTEGER`

The respective parameters for either Leiden(CPM) (`-c leiden`) or IKC (`-c ikc`). Only at most one should be specified, and for modularity optimization neither should be specified.

### `-o, --output OUTPUT_PREFIX`

The output prefix. Two files will be produced, first the `OUTPUT_PREFIX` will have a file denoting the last cluster a node has been in, and `{OUTPUT_PREFIX}.tree.json` is a serialized tree denoting the history of the execution of the algorithm. See also [converting the output to more parsable formats](#format-conversion).

### `-t, --threshold TEXT`

Threshold expression. `cm` guarantees that the output clustering all have clusters that are above a specific threshold. We list some examples for `-t` below:

```bash
# each line denotes a valid example for "-t"
2 # connectivity must >= 2
0.1mcd # connectivity must >= 0.1 MCD, MCD the minimum intra-cluster degree
0.1mcd+42 # linear combinations are allowed to some extent
1log10 # >= log10 of size of cluster
99log10+0.0002mcd+1 # combinations like this are allowed
```

### `-d, --working-dir TEXT`

Entirely optional; specifies where `cm` should store its temporary files.

## Example commands

```bash
# Leiden, CPM optimization (resolution = 0.1)
# BUT, the output clusters must satisfy global connectivity >= 1 * log10(n), n the size of cluster
cm -i graph.tsv -c leiden -g 0.1 -t 1log10 -o leiden_clus.txt
```

```bash
# IKC, k = 10
# BUT, the output clusters must satisfy global connectivity >= 0.1 * mcd, MCD the minimum intra-cluster degree among all nodes
# we additionally use an existing IKC clustering (ikc_output.csv) as the starting point to be modified
cm -i graph.tsv -c ikc -k 10 -t 0.1mcd -e ikc_output.csv -o ikc_clus.txt
```

<!-- ```shell
# clone the repo, and cd into the repo
poetry install # install the hm01 script in PATH
hm01 -i /srv/local/shared/external/dbid/george/exosome_dimensions_wedell_retraction-depleted_jc250-corrected_no_header.tsv -c ikc -k 10 -t 0.1mcd -d working_dir -o clusters.txt
``` -->

## Format Conversion

The default output of `cm` contains the entire history of the execution of the algorithm. This format allows preservation of much information, but often times for data analysis, only knowing the clustering *before* modifying the connectivity (i.e., as if just running the base method) and *after* modifying the connectivity is enough. These two sets of clusters can be obtained from `cm` using the specialized tool `cm2universal`:

```bash
# INPUT_GRAPH is the same INPUT_GRAPH
# CM_OUTPUT_PREFIX is the same output prefix of `cm`, i.e., `{CM_OUTPUT_PREFIX}.tree.json` and `CM_OUTPUT_PREFIX` are existing files
# CLUSTERS_OUTPUT_PREFIX is where you want the converted clusters
cm2universal -g INPUT_GRAPH -i CM_OUTPUT_PREFIX -o CLUSTERS_OUTPUT_PREFIX
```

Two files will be generated: `{CLUSTERS_OUTPUT_PREFIX}.original.json` and `{CLUSTERS_OUTPUT_PREFIX}.extant.json`, containing the original and after clusters respectively. The `json` files use the so-called "universal" new-line delimited JSON format, looking like this:

```json
{"label": "0", "nodes": [0, 3, 7, 9], "connectivity": 1}
{"label": "46", "nodes": [5765736, 4717164, 14154348, 3144303, 6290035, 3668596, 1571445, 2620022, 4717176], "connectivity": 2}
```

These files can be directly parsed (each line is a cluster, `label` the cluster name, `nodes` the node ids of that cluster, `connectivity` the edge connectivity) or can be paired with the data science tool [belinda](https://github.com/illinois-or-research-analytics/belinda).

## Development

We use [Poetry](https://python-poetry.org/) to manage our progress and follow the Poetry conventions. See below for some example commands:

```bash
poetry install # install networkit and co
poetry run pytest # run tests
```


<!-- ## Algorithm
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
``` -->