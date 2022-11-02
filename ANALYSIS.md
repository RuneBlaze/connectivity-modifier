Performing Analysis
===================

All below commands are assumed to be prefixed with `poetry run`.

## Visualize the tree

`hm01` outputs also a tree file (suffixed `.tree.json`). The tree can be visualized by

```bash
python3 analysis_scripts/visualize_history.py -i tree_file.tree.json -o output_prefix [-n num_nodes]
# the output will be at output_prefix.pdf

# num_nodes is the maximum amount of depth-1 node that we visualize, defaults to 30
```

## Compute Statistics

A specialized script `impact_hm01` is exposed for calculating statistics

```bash
impact_hm01 -g edgelist_file_background_network -i clustering_path -o output_prefix
```

Two sets of CSV files will be written

 - `output_prefix.extant.csv`: statistics about the surviving clusters
 - `output_prefix.original.csv`: statistics about the original clusters

"High degree" is defined as 90-percentile degree.


### Print statistics as LaTeX

The script `analysis_scripts/summary_statistics_printer.py` can be used to print both set of summary statistics like this to a LaTeX formatted table:

```bash
python3 analysis_scripts/summary_statistics_printer.py -i output_prefix # outputs to stdout
```

However, this script is less polished than the others. I had to frequently adjust the output as I see fit.