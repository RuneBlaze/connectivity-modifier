from genericpath import isfile
import typer
import pandas as pd
import os

def reformat_nonfloat(s):
    return '-'.join([str(int(float(e))) if int(float(e)) == float(e) else str(e) for e in s.split("-")])

def main(
    input: str = typer.Option(..., "--input_prefix", "-i"),
):
    columns = ["num_clusters", "node_coverage", "edge_coverage", "top_singleton_nodes", "min_cut_sizes", "cluster_sizes"]
    dfs = {}
    for suffix in ["ancient", "original", "extant"]:
        fn = f"{input}.{suffix}.csv"
        if os.path.isfile(fn):
            df = pd.read_csv(fn)[columns]
            df["type"] = dict(ancient="original",original="preprocessed",extant="after")[suffix]
            dfs[suffix] = df
    df = pd.concat(dfs.values())
    df = df[["type"] + columns]
    df["min_cut_sizes"] = df["min_cut_sizes"].apply(reformat_nonfloat)
    df["cluster_sizes"] = df["cluster_sizes"].apply(reformat_nonfloat)
    # format node_coverage, edge_coverage, top_singleton_nodes as percentages in LaTeX
    for col in ["node_coverage", "edge_coverage", "top_singleton_nodes"]:
        df[col] = df[col].apply(lambda x: f"{x:.2%}")
    # print LaTeX table. Before and After
    print(df.rename(columns={
        "num_clusters": "# clusters",
        "node_coverage": "node cov.",
        "edge_coverage": "edge cov.",
        "top_singleton_nodes": "high deg. singletons",
        "min_cut_sizes": "edge conn.",
        "cluster_sizes": "cluster size",
    }).to_latex(index=False, column_format="lrrrrrr"))

def entry_point():
    typer.run(main)

if __name__ == "__main__":
    entry_point()
