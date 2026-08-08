from pathlib import Path

import typer

from kgm.documentor import TableFormats, catalogue, table

app = typer.Typer(help="Create documentation from a KGM")


@app.command(
    name="table",
    help="Create a Markdown or ASCIIDOC table for the resources listed in a KGM",
)
def table_command(
    manifest: Path = typer.Argument(
        ..., help="The path of the KGM file to be documented"
    ),
    table_format: TableFormats = typer.Option(
        TableFormats.markdown,
        "--format",
        "-f",
        help="The format of the table to be created",
    ),
) -> None:
    print(table(manifest, table_format))


@app.command(
    name="catalogue",
    help="Add the resources listed in a KGM to a catalogue RDF file",
)
def catalogue_command(
    manifest: Path = typer.Argument(
        ..., help="The path of the KGM file to be documented"
    ),
) -> None:
    print(catalogue(manifest).serialize(format="longturtle"))
