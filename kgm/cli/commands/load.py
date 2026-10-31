from pathlib import Path
from typing import Annotated

import typer

from kgm.endpoint import endpoint_errors
from kgm.loader import load
from kgm.rdf import load_dataset
from kgm.syncer import get_sync_dataset

app = typer.Typer(help="Load a KGM's content into a file or DB")


@app.command(name="sparql", help="Load a KGM's resources into a SPARQL Endpoint")
def sparql_command(
    manifest: Path = typer.Argument(..., help="The path of the KGM file to be loaded"),
    endpoint: str = typer.Argument(..., help="The URL of the SPARQL Endpoint"),
    username: Annotated[
        str, typer.Option("--username", "-u", help="SPARQL Endpoint username.")
    ] = None,
    password: Annotated[
        str, typer.Option("--password", "-p", help="SPARQL Endpoint password.")
    ] = None,
    timeout: Annotated[
        int, typer.Option("--timeout", "-t", help="Timeout per request")
    ] = 60,
) -> None:
    with endpoint_errors(endpoint):
        load(
            manifest,
            sparql_endpoint=endpoint,
            sparql_username=username,
            sparql_password=password,
            timeout=timeout,
        )


@app.command(name="file", help="Load a KGM's resources into a single RDF quads file")
def file_command(
    manifest: Path = typer.Argument(..., help="The path of the KGM file to be loaded"),
    file: Path = typer.Argument(
        ..., help="The path of the quads file (.nq for N-Quads or .trig for TriG)"
    ),
) -> None:
    formats = {".nq": "nquads", ".trig": "trig"}
    output_format = formats.get(file.suffix.lower())
    if output_format is None:
        raise typer.BadParameter(
            "Use .nq for N-Quads or .trig for TriG", param_hint="file"
        )

    dataset = get_sync_dataset(manifest)
    if file.is_file():
        dataset += load_dataset(file, format=output_format)
    dataset.serialize(destination=file, format=output_format)
