from pathlib import Path

import typer

from kgm.cli.app import app
from kgm.validator import validate


@app.command(
    name="validate", help="Validate the structure and content of a KGM"
)
def validate_command(
    manifest: Path = typer.Argument(
        ..., help="The path of the KGM file to be validated"
    ),
) -> None:
    validate(manifest)
