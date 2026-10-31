"""Kurra SPARQL queries using HTTPX2 clients and compatible JSON decoding."""

from contextlib import ExitStack
from pathlib import Path

import httpx2
from kurra.sparql import query as kurra_query
from kurra.utils import convert_sparql_json_to_python, is_select_or_ask_query
from rdflib import Dataset, Graph


def query(
    p: Path | str | Graph | Dataset,
    q: str | Path,
    namespaces: dict[str, str] | None = None,
    http_client: httpx2.Client | None = None,
    return_format: str = "original",
    return_bindings_only: bool = False,
):
    """Keep Kurra's query interface without passing new response types to its decoder.

    Kurra currently recognises only legacy HTTPX Response objects. Decode remote
    SELECT/ASK results from JSON text so HTTPX2 clients work without global aliases.
    """
    if isinstance(q, Path):
        q = q.read_text()
    elif isinstance(q, str) and len(q) < 260 and Path(q).is_file():
        q = Path(q).read_text()
    with ExitStack() as stack:
        if http_client is None:
            http_client = stack.enter_context(httpx2.Client())
        decode_json = (
            isinstance(p, str)
            and p.startswith(("http://", "https://"))
            and return_format == "python"
            and is_select_or_ask_query(q)
        )
        result = kurra_query(
            p,
            q,
            namespaces=namespaces,
            http_client=http_client,
            return_format="original" if decode_json else return_format,
            return_bindings_only=return_bindings_only,
        )
        if decode_json:
            return convert_sparql_json_to_python(result, return_bindings_only)
        return result
