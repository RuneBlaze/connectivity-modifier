import typer
import pandas as pd

def main(
    input: str = typer.Option(..., "--input_prefix", "-i"),
):
    columns = ["num_clusters", "node_coverage", "edge_coverage", "top_singleton_nodes", "min_cut_sizes", "cluster_sizes"]
    original_stats = pd.read_csv(f"{input}.original.csv")[columns]
    extant_stats = pd.read_csv(f"{input}.extant.csv")[columns]
    # format node_coverage, edge_coverage, top_singleton_nodes as percentages in LaTeX
    for col in ["node_coverage", "edge_coverage", "top_singleton_nodes"]:
        original_stats[col] = original_stats[col].apply(lambda x: f"{x:.2%}")
        extant_stats[col] = extant_stats[col].apply(lambda x: f"{x:.2%}")
    # print LaTeX table. Before and After
    print(original_stats.to_latex(index=False, escape=False))
    print(extant_stats.to_latex(index=False, escape=False))

def entry_point():
    typer.run(main)

if __name__ == "__main__":
    entry_point()
