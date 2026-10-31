"""RDF loading with source-aware parser errors."""

from contextlib import contextmanager, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
from xml.sax import SAXParseException

import httpx2
from kurra.file import FailOnChangeError, reformat
from kurra.utils import RDF_SUFFIX_MAP
from kurra.utils import load_graph as kurra_load_graph
from rdflib import Dataset, Graph
from rdflib.exceptions import ParserError


class RDFParseError(SyntaxError):
    """An RDF parser failure annotated with the input file or URL."""


@contextmanager
def parsing_source(source: Path | str, kind: str = "RDF file"):
    try:
        yield
    except (SyntaxError, ParserError, ValueError, SAXParseException) as error:
        detail = error.__cause__ if isinstance(error, RDFParseError) else error
        raise RDFParseError(f"Failed to load {kind} {source}:\n{detail}") from error


def load_graph(source: Path | str | Graph) -> Graph:
    if isinstance(source, Path) and source.is_dir():
        graph = Graph()
        for file in source.glob("*.ttl"):
            if file.is_file():
                graph += load_graph(file)
        return graph
    with parsing_source(source):
        return kurra_load_graph(source)


def load_dataset(source: Path, format: str) -> Dataset:
    with parsing_source(source):
        return Dataset().parse(source, format=format)


def check_rdf_syntax(source: Path | str) -> None:
    """Run Kurra's reformat --check parser without changing the source file.

    Formatting differences are irrelevant to syntax validation. Non-RDF files
    are skipped; remote RDF is identified by its suffix or response media type.
    """
    with TemporaryDirectory(prefix="kgm-rdf-check-") as directory:
        temporary = Path(directory)
        if isinstance(source, str) and source.startswith(("http://", "https://")):
            response = httpx2.get(source, follow_redirects=True)
            response.raise_for_status()
            suffix = Path(urlsplit(source).path).suffix.lower()
            if suffix not in RDF_SUFFIX_MAP:
                media_type = (
                    response.headers.get("content-type", "").split(";")[0].strip()
                )
                suffix = next(
                    (ext for ext, mime in RDF_SUFFIX_MAP.items() if mime == media_type),
                    "",
                )
            if suffix not in RDF_SUFFIX_MAP:
                return
            path = temporary / f"remote{suffix}"
            path.write_bytes(response.content)
        else:
            path = Path(source)
            if path.suffix.lower() not in RDF_SUFFIX_MAP:
                return

        with parsing_source(source), redirect_stdout(StringIO()):
            try:
                reformat(path, check=True, output_filename=temporary / "check-output")
            except FailOnChangeError:
                pass
