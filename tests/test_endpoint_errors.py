from importlib import import_module
from unittest.mock import Mock

import httpx
import pytest
from rdflib import Graph, URIRef
from typer.testing import CliRunner

from kgm.cli import app
from kgm.definednamespaces import MRR
from kgm.endpoint import SPARQLEndpointError, endpoint_errors


@pytest.mark.parametrize("command", ["sync", "load"])
@pytest.mark.parametrize(
    "failure,reason",
    [
        ("connect", "connection failed"),
        ("timeout", "request timed out"),
        (404, "HTTP 404"),
        (503, "HTTP 503"),
    ],
)
def test_endpoint_failure_is_printed_without_traceback(
    monkeypatch, tmp_path, command, failure, reason
):
    endpoint = "https://example.com/missing/sparql"

    def respond(request):
        if failure == "connect":
            raise httpx.ConnectError("Connection refused", request=request)
        if failure == "timeout":
            raise httpx.ReadTimeout("Read timed out", request=request)
        return httpx.Response(failure, text="<html>Verbose server error</html>")

    syncer = import_module("kgm.syncer")
    monkeypatch.setattr(
        syncer,
        "get_manifest_paths_and_graph",
        lambda manifest: (manifest, tmp_path, Graph()),
    )
    monkeypatch.setattr(
        syncer,
        "denormalise_artifacts",
        lambda manifest: {
            tmp_path / "catalogue.nt": {
                "role": MRR.CatalogueData,
                "main_entity": URIRef("https://example.com/catalogue"),
                "sync": True,
            }
        },
    )
    upload = Mock(
        side_effect=AssertionError("Should not upload after endpoint failure")
    )
    monkeypatch.setattr(syncer, "upload", upload)
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        module = import_module(
            "kgm.cli.commands.sync" if command == "sync" else "kgm.loader"
        )
        monkeypatch.setattr(module, "make_httpx_client", lambda *args: client)
        args = (
            ["sync", "manifest.nt", endpoint]
            if command == "sync"
            else ["load", "sparql", "manifest.nt", endpoint]
        )
        result = CliRunner().invoke(app, args)

    assert result.exit_code == 1
    assert (
        result.stderr.strip()
        == f"Error: SPARQL Endpoint not accessible: {endpoint} ({reason})"
    )
    assert "Traceback" not in result.output
    assert "Verbose server error" not in result.output
    assert result.stdout == ""
    upload.assert_not_called()


def test_unrelated_runtime_error_is_preserved():
    error = RuntimeError("Unexpected data failure")
    with pytest.raises(RuntimeError) as exc_info:
        with endpoint_errors("https://example.com/sparql"):
            raise error
    assert exc_info.value is error


def test_other_hosts_connection_error_is_preserved():
    error = httpx.ConnectError(
        "Background unavailable",
        request=httpx.Request("GET", "https://background.example.com/sparql"),
    )
    with pytest.raises(httpx.ConnectError) as exc_info:
        with endpoint_errors("https://example.com/sparql"):
            raise error
    assert exc_info.value is error


def test_endpoint_message_excludes_credentials_and_response_body():
    with pytest.raises(SPARQLEndpointError) as exc_info:
        with endpoint_errors("https://user:secret@example.com/sparql?token=private"):
            raise RuntimeError("ERROR 403: verbose server response")
    assert (
        str(exc_info.value)
        == "SPARQL Endpoint not accessible: https://example.com/sparql (HTTP 403)"
    )
    assert isinstance(exc_info.value.__cause__, RuntimeError)
