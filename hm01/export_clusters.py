from __future__ import annotations
# export clusters to the belinda expected format
from typing import List, Optional, Sequence, Union
import typer

def main(
    input: str = typer.Option(..., "--input", "-i"),
    graph_path: str = typer.Option(..., "--graph", "-g"),
    output: str = typer.Option(..., "--output_prefix", "-o"),
    ancient_clustering_path: Optional[str] = typer.Option(None, "--ancient_clustering"),
):
    pass


def entry_point():
    typer.run(main)


if __name__ == "__main__":
    entry_point()