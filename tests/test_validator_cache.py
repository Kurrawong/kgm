from pathlib import Path
from unittest.mock import Mock

import kurra.shacl
import pytest
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import SDO

from kgm import validator


@pytest.fixture
def isolated_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    sync = kurra.shacl.sync_validators

    def selective_sync(*args, **kwargs):
        assert kwargs.get("validator_iris"), "Must not sync all validators"
        return sync(*args, **kwargs)

    monkeypatch.setattr(
        kurra.shacl,
        "sync_validators",
        selective_sync,
    )
    monkeypatch.setattr(
        kurra.shacl,
        "query",
        Mock(
            return_value=[
                {"p": iri}
                for iri in [
                    "https://example.com/first",
                    "https://example.com/second",
                    "https://example.com/validator",
                    "https://prez.dev/manifest-validator",
                    "https://example.com/unneeded",
                ]
            ]
        ),
    )
    return tmp_path / ".kurra"


def shapes(iri):
    graph = Graph(identifier=URIRef(iri))
    graph.add((URIRef(iri), SDO.name, Literal("Test validator")))
    return graph


def test_fetch_only_missing_validators(monkeypatch, isolated_cache):
    fetch = Mock(side_effect=lambda endpoint, iri, **kwargs: shapes(iri))
    monkeypatch.setattr(kurra.shacl, "gsp_get", fetch)
    first = "https://example.com/first"
    second = "https://example.com/second"

    validator._ensure_validator(first)
    validator._ensure_validator(second)
    validator._ensure_validator(first)
    validator._ensure_validator(second)

    assert [call.args[1] for call in fetch.call_args_list] == [first, second]
    assert set(kurra.shacl.list_local_validators()) == {first, second}
    # The cache can be consumed by Kurra without triggering its bulk fallback.
    assert kurra.shacl.validate(Graph(), first)[0]


def test_unknown_validator_not_cached(monkeypatch, isolated_cache):
    fetch = Mock(side_effect=AssertionError("Unknown validator must not be fetched"))
    monkeypatch.setattr(kurra.shacl, "gsp_get", fetch)
    with pytest.raises(validator.ManifestValidationError, match="not known"):
        validator._ensure_validator("https://example.com/missing")
    assert not isolated_cache.exists()


def test_local_conformance_fetches_only_manifest_validator(monkeypatch, isolated_cache):
    fetch = Mock(side_effect=lambda endpoint, iri, **kwargs: shapes(iri))
    monkeypatch.setattr(kurra.shacl, "gsp_get", fetch)
    manifest = Path(__file__).parent / "validator/manifest-conformance-own.ttl"
    with pytest.raises(validator.ManifestValidationError, match="artifact.*invalid"):
        validator.validate(manifest)
    assert [call.args[1] for call in fetch.call_args_list] == [
        "https://prez.dev/manifest-validator"
    ]


def test_remote_conformance_is_fetched_once(monkeypatch, isolated_cache):
    from rdflib.namespace import DCTERMS

    manifest = Path(__file__).parent / "validator/manifest-conformance-own.ttl"
    load_graph = validator.load_graph
    graph = load_graph(manifest)
    iri = URIRef("https://example.com/validator")
    for subject, old in list(graph.subject_objects(DCTERMS.conformsTo)):
        graph.remove((subject, DCTERMS.conformsTo, old))
        graph.add((subject, DCTERMS.conformsTo, iri))
    graph.add((URIRef("https://example.com/other"), DCTERMS.conformsTo, iri))
    monkeypatch.setattr(
        validator,
        "load_graph",
        lambda path: graph if path == manifest else load_graph(path),
    )
    fetch = Mock(side_effect=lambda endpoint, iri, **kwargs: shapes(iri))
    monkeypatch.setattr(kurra.shacl, "gsp_get", fetch)

    assert validator.validate(manifest)
    assert validator.validate(manifest)
    assert [call.args[1] for call in fetch.call_args_list] == [
        "https://prez.dev/manifest-validator",
        str(iri),
    ]
