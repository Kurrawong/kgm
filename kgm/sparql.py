"""Kurra SPARQL queries using managed HTTPX2 clients."""

from contextlib import ExitStack
from pathlib import Path

import httpx2
from kurra.sparql import query as kurra_query
from rdflib import Dataset, Graph


def query(
    p: Path | str | Graph | Dataset,
    q: str | Path,
    namespaces: dict[str, str] | None = None,
    http_client: httpx2.Client | None = None,
    return_format: str = "original",
    return_bindings_only: bool = False,
):
    """Use Kurra's HTTPX2 query handling, closing clients created here."""
    with ExitStack() as stack:
        if http_client is None:
            http_client = stack.enter_context(httpx2.Client())
        return kurra_query(
            p,
            q,
            namespaces=namespaces,
            http_client=http_client,
            return_format=return_format,
            return_bindings_only=return_bindings_only,
        )
