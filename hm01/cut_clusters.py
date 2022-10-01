import typer
from enum import Enum
from typing import Optional


class Clusterer(str, Enum):
    leiden = "leiden"
    ikc = "ikc"


def main(
    input: str = typer.Option(..., "--input", "-i"),
    clusterer: Clusterer = typer.Option(..., "--clusterer", "-c"),
    k: int = typer.Option(-1, "--k", "-k"),
    resolution: float = typer.Option(-1, "--resolution", "-r"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
):
    pass


if __name__ == "__main__":
    typer.run(main)
