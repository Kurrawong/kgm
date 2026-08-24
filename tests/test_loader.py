import warnings
from pathlib import Path

import httpx
import pytest
from kurra.db.gsp import upload, delete
from kurra.sparql import query
from typer.testing import CliRunner

from kgm.loader import ReturnDatatype, load

runner = CliRunner()


def test_load_delegates_to_sync(monkeypatch):
    calls = []

    def fake_sync(manifest, endpoint, http_client):
        calls.append((manifest, endpoint, http_client))
        return {"delegated": True}

    monkeypatch.setattr("kgm.loader.sync", fake_sync)

    manifest = Path("manifest.ttl")
    with pytest.warns(
        DeprecationWarning,
        match=r"use sync\(\) instead.*removed in kgm v3",
    ):
        result = load(manifest, sparql_endpoint="https://example.com/sparql")

    assert result == {"delegated": True}
    assert calls[0][0:2] == (manifest, "https://example.com/sparql")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"destination_file": Path("output.trig")},
        {"return_data_type": ReturnDatatype.graph},
        {"return_data_type": ReturnDatatype.dataset},
    ],
)
def test_load_rejects_modes_sync_cannot_alias(kwargs):
    with pytest.raises(NotImplementedError, match="only supports a SPARQL endpoint"):
        load(Path("manifest.ttl"), **kwargs)


def test_load_only_one_set():
    warnings.filterwarnings(
        "ignore", category=DeprecationWarning
    )  # ignore RDFLib's ConjunctiveGraph warning

    manifest = Path(Path(__file__).parent / "demo-vocabs/manifest.ttl")

    with pytest.raises(ValueError):
        load(manifest)

    with pytest.raises(NotImplementedError):
        load(
            manifest,
            sparql_endpoint="http://fake.com",
            destination_file=Path("some-fake-path"),
        )

    with pytest.raises(NotImplementedError):
        load(
            manifest,
            destination_file=Path("some-fake-path"),
            return_data_type=ReturnDatatype.graph,
        )

    with pytest.raises(ValueError):
        load(manifest, return_data_type="hello")

    with pytest.raises(NotImplementedError):
        load(manifest, destination_file=Path("temp.trig"))


def test_fuseki_query(sparql_endpoint):
    TESTING_GRAPH = "https://example.com/testing-graph"

    data = """
            PREFIX ex: <http://example.com/>

            ex:a ex:b ex:c .
            ex:a2 ex:b2 ex:c2 .
            """

    upload(sparql_endpoint, data, TESTING_GRAPH, False)

    q = """
        SELECT (COUNT(*) AS ?count) 
        WHERE {
          GRAPH <XXX> {
            ?s ?p ?o
          }
        }        
        """.replace("XXX", TESTING_GRAPH)

    r = query(sparql_endpoint, q, return_format="python", return_bindings_only=True)

    assert r[0]["count"] == 2

    delete(sparql_endpoint, TESTING_GRAPH)

    r = query(sparql_endpoint, q)

    q = """
        SELECT (COUNT(*) AS ?count) 
        WHERE {
          GRAPH <XXX> {
            ?s ?p ?o
          }
        }        
        """.replace("XXX", TESTING_GRAPH)

    r = query(sparql_endpoint, q, return_format="python", return_bindings_only=True)

    assert r[0]["count"] == 0


def test_load_to_quads_file():
    warnings.filterwarnings(
        "ignore", category=DeprecationWarning
    )  # ignore RDFLib's ConjunctiveGraph warning
    manifest = Path(__file__).parent / "demo-vocabs" / "manifest.ttl"
    results_file = Path(__file__).parent / "results.trig"

    with pytest.raises(NotImplementedError):
        load(manifest, sparql_endpoint=None, destination_file=results_file)


def test_load_to_fuseki(sparql_endpoint):
    manifest = Path(__file__).parent / "demo-vocabs" / "manifest.ttl"
    load(manifest, sparql_endpoint=sparql_endpoint)

    q = """
        SELECT (COUNT(DISTINCT ?g) AS ?count)
        WHERE {
            GRAPH ?g {
                ?s ?p ?o 
            }
        }      
        """

    r = query(sparql_endpoint, q, return_format="python", return_bindings_only=True)

    assert r[0]["count"] == 5


def test_load_to_fuseki_basic_auth(sparql_endpoint):
    manifest = Path(__file__).parent / "demo-vocabs" / "manifest.ttl"
    load(
        manifest,
        sparql_endpoint=sparql_endpoint,
        sparql_username="admin",
        sparql_password="admin",
    )

    q = """
        SELECT (COUNT(DISTINCT ?g) AS ?count)
        WHERE {
            GRAPH ?g {
                ?s ?p ?o 
            }
        }      
        """
    client = httpx.Client(auth=("admin", "admin"))
    r = query(
        sparql_endpoint,
        q,
        return_format="python",
        return_bindings_only=True,
        http_client=client,
    )

    assert r[0]["count"] == 5


def test_load_with_artifact_bn():
    warnings.filterwarnings(
        "ignore", category=DeprecationWarning
    )  # ignore RDFLib's ConjunctiveGraph warning
    manifest = Path(__file__).parent / "demo-vocabs" / "manifest-mainEntity.ttl"
    results_file = Path(__file__).parent / "results.trig"

    with pytest.raises(NotImplementedError):
        load(manifest, destination_file=results_file)


def test_load_returns_dataset():
    manifest = Path(__file__).parent / "demo-vocabs" / "manifest-mainEntity.ttl"
    with pytest.raises(NotImplementedError):
        load(manifest, return_data_type=ReturnDatatype.dataset)


# TODO: not working
# def test_load_cli_file(fs):
#     warnings.filterwarnings(
#         "ignore", category=DeprecationWarning
#     )  # ignore RDFLib's ConjunctiveGraph warning
#
#     fake_file = fs.create_file(Path(__file__).parent.resolve() / "temp.trig")
#
#     manifest = Path(__file__).parent / "demo-vocabs/manifest.ttl"
#     tmp_output_file = Path(__file__).parent.resolve() / "temp.trig"
#     runner.invoke(
#         app,
#         [
#             "load",
#             "file",
#             manifest,
#             fake_file.path
#         ],
#     )
#
#     output = fake_file.read_text()
#
#     assert output.count(" {") == 5
#
#     # Path("temp.trig").unlink(missing_ok=True)


# TODO: not working
# def test_load_cli_sparql(sparql_endpoint):
#     warnings.filterwarnings(
#         "ignore", category=DeprecationWarning
#     )  # ignore RDFLib's ConjunctiveGraph warning
#
#     manifest = Path(__file__).parent / "demo-vocabs/manifest.ttl"
#     response = runner.invoke(
#         app,
#         [
#             "load",
#             "sparql",
#             manifest,
#             sparql_endpoint,
#             "-u",
#             "admin",
#             "-p",
#             "admin"
#         ],
#     )
#
#     print(response.stdout)
#
#     q = """
#         SELECT (COUNT(DISTINCT ?g) AS ?count)
#         WHERE {
#             GRAPH ?g {
#                 ?s ?p ?o
#             }
#         }
#         """
#     client = httpx.Client(auth=("admin", "admin"))
#     r = query(
#         sparql_endpoint,
#         q,
#         return_format="python",
#         return_bindings_only=True,
#         http_client=client,
#     )
#
#     count = int(r[0]["count"])
#
#     assert count == 5
