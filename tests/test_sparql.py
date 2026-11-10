import httpx2
import pytest
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, SDO

from kgm.sparql import query
from kgm.utils import make_httpx2_client


@pytest.mark.parametrize("value", [True, False])
def test_httpx2_ask_results(value):
    def respond(request):
        return httpx2.Response(200, json={"head": {}, "boolean": value})

    with make_httpx2_client(transport=httpx2.MockTransport(respond)) as client:
        assert (
            query(
                "https://example.com/sparql",
                "ASK { ?s ?p ?o }",
                http_client=client,
                return_format="python",
                return_bindings_only=True,
            )
            is value
        )
        assert not client.is_closed


def test_httpx2_select_results():
    response = {
        "head": {"vars": ["s"]},
        "results": {
            "bindings": [
                {"s": {"type": "uri", "value": "https://example.com/resource"}}
            ]
        },
    }
    with make_httpx2_client(
        transport=httpx2.MockTransport(
            lambda request: httpx2.Response(200, json=response)
        )
    ) as client:
        result = query(
            "https://example.com/sparql",
            "SELECT ?s WHERE { ?s ?p ?o }",
            http_client=client,
            return_format="python",
            return_bindings_only=True,
        )
    assert result == [{"s": "https://example.com/resource"}]


def test_httpx2_construct_results():
    data = (
        "<https://example.com/resource> "
        "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type> "
        "<https://schema.org/Dataset> ."
    )
    with make_httpx2_client(
        transport=httpx2.MockTransport(lambda request: httpx2.Response(200, text=data))
    ) as client:
        result = query(
            "https://example.com/sparql",
            "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }",
            http_client=client,
            return_format="python",
        )
    assert (URIRef("https://example.com/resource"), RDF.type, SDO.Dataset) in result


def test_local_query_keeps_kurra_behaviour():
    graph = Graph()
    graph.add((URIRef("https://example.com/resource"), RDF.type, SDO.Dataset))
    assert (
        query(
            graph, "ASK { ?s ?p ?o }", return_format="python", return_bindings_only=True
        )
        is True
    )


def test_client_factory_returns_httpx2_client():
    with make_httpx2_client("user", "password", 10) as client:
        assert isinstance(client, httpx2.Client)
        assert isinstance(client.auth, httpx2.BasicAuth)
        assert client.timeout.read == 10
