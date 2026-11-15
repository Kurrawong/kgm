from pathlib import Path

import typer

from kgm.cli.app import app
from kgm.validator import validate


@app.command(
    name="validate",
    help="Validate the structure and content of a Manfest file and the content it links to",
)
def validate_command(
    manifest: Path = typer.Argument(
        ..., help="The path of the Manifest file to be validated"
    ),
    rdf: bool = typer.Option(
        False,
        "--rdf",
        "-r",
        help="Parse all referenced RDF files to check their syntax",
    ),
    use_rudof: bool = typer.Option(
        False, "--use-rudof", "-x", help="Use Rudof for SHACL validation"
    ),
) -> None:
    validate(manifest, rdf=rdf, use_rudof=use_rudof)
