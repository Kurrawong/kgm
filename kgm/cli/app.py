import logging
import os
import sys
from pathlib import Path
from typing import Annotated

import typer
from typer.core import TyperGroup

from kgm import __version__
from kgm.cli.console import console
from kgm.endpoint import SPARQLEndpointError
from kgm.rdf import RDFParseError
from kgm.utils import print_local_version_indicators


class KGMGroup(TyperGroup):
    def list_commands(self, ctx: typer.Context) -> list[str]:
        return sorted(super().list_commands(ctx))

    def invoke(self, ctx):
        try:
            return super().invoke(ctx)
        except (RDFParseError, SPARQLEndpointError) as error:
            typer.echo(f"Error: {error}", err=True)
            raise typer.Exit(code=1) from error


# Configure logging
def setup_logging():
    """Set up logging configuration for the CLI."""
    # Get log level from environment or default to WARNING
    log_level_str = os.getenv("KGM_LOG_LEVEL", "WARNING").upper()
    log_level = getattr(logging, log_level_str, logging.WARNING)

    # Create logger
    logger = logging.getLogger("kgm")
    logger.setLevel(log_level)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d %(message)s"
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)


# Set up logging when the module is imported
setup_logging()

app = typer.Typer(
    cls=KGMGroup,
    invoke_without_command=True,
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main(
    version: Annotated[bool, typer.Option("--version", "-v", is_eager=True)] = False,
):
    """KGM top-level Command Line Interface. Ask for help (-h) for each Command"""
    if version:
        console.print(__version__)
        raise typer.Exit()


@app.command(
    name="versiontest",
    help=(
        "Prints the version information that kgm sync uses when attempting "
        "to synchronise a file with a SPARQL endpoint"
    ),
)
def versiontest_command(
    file: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, help="Path to a local RDF file"),
    ],
    manifest: Annotated[
        Path | None,
        typer.Argument(
            exists=True,
            dir_okay=False,
            help="Optional manifest file with information about the file",
        ),
    ] = None,
) -> None:
    try:
        print_local_version_indicators(file, manifest)
    except ValueError as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error
