"""
Either creates an n-quads files containing the content of a Manifest file or uploads the content to Fuseki.

It creates:

 1. A Named Graph for each resource using the item's IRI as the graph IRI
 2. A Named Graph for the catalogue, either using the catalogue's IRI as the graph IRI + "-catalogue" if given, or by making one up - a Blank Node
 3. All the triples in resources with roles mrr:CompleteCatalogueAndResourceLabels & mrr:IncompleteCatalogueAndResourceLabels within a Named Graph with IRI <https://background>
 4. An Olis Virtual Graph, <https://olis.dev/VirtualGraph> object using the catalogue IRI, if give, which is as an alias for all the Named Graphs from 1., 2. & 3.
 5. Multiple entries in the System Graph - Named Graph with IRI <https://olis.dev/SystemGraph> - for each Named and the Virtual Graph from 1., 2. & 3.

Run this script with the -h flag for more help, i.e. ~$ python loader.py -h
"""

import sys
from enum import Enum
from getpass import getpass
from pathlib import Path

from rdflib import Dataset, Graph

from kgm.syncer import sync
from kgm.utils import make_httpx_client


class ReturnDatatype(str, Enum):
    graph = "graph"
    dataset = "dataset"
    none = None


def load(
    manifest: Path | tuple[Path, Path, Graph],
    sparql_endpoint: str = None,
    sparql_username: str = None,
    sparql_password: str = None,
    timeout: int = 60,
    destination_file: Path = None,
    return_data_type: ReturnDatatype = ReturnDatatype.none,
) -> None | Graph | Dataset:
    """Loads a catalogue of data from a Manifest file, whose content are valid according to the KGM Model
    (https://kurrawong.github.io/prez.dev/manifest/) either into a specified quads file in the Trig format, or into a
    given SPARQL Endpoint."""

    if not isinstance(return_data_type, ReturnDatatype):
        raise ValueError(
            f"Invalid return_data_type value. Must be one of {', '.join([x for x in ReturnDatatype])}"
        )

    if destination_file is not None or return_data_type != ReturnDatatype.none:
        raise NotImplementedError(
            "load() is now an alias for sync(), which only supports a SPARQL "
            "endpoint; destination_file and return_data_type are not supported"
        )

    if sparql_endpoint is None:
        raise ValueError("A sparql_endpoint must be specified")

    if sparql_username and not sparql_password:
        if not sys.stdin.isatty():
            raise ValueError("A password must be given if a sparql username is set")
        sparql_password = getpass()

    return sync(
        manifest,
        sparql_endpoint,
        make_httpx_client(sparql_username, sparql_password, timeout),
    )
