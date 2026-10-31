from importlib import import_module
from pathlib import Path
from unittest.mock import Mock

import pytest
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, PROF, RDF, SDO
from typer.testing import CliRunner

from kgm.cli import app
from kgm.definednamespaces import MRR, PREZ
from kgm.rdf import RDFParseError, load_graph
from kgm.validator import validate


@pytest.mark.parametrize(
    "suffix,content",
    [(".nt", "not an RDF triple"), (".jsonld", "{broken json"), (".rdf", "<broken>")],
)
def test_parse_error_keeps_source_and_original_error(tmp_path, suffix, content):
    source = tmp_path / f"broken{suffix}"
    source.write_text(content)
    with pytest.raises(RDFParseError) as exc_info:
        load_graph(source)
    assert str(source) in str(exc_info.value)
    assert str(exc_info.value.__cause__) in str(exc_info.value)
    assert exc_info.value.__cause__ is not None


def test_manifest_parse_error_is_printed_with_filename(tmp_path):
    source = tmp_path / "manifest.nt"
    source.write_text("invalid manifest RDF")
    with pytest.raises(RDFParseError, match="manifest file") as exc_info:
        validate(source)
    assert str(source) in str(exc_info.value)
    assert "Invalid line" in str(exc_info.value)

    result = CliRunner().invoke(app, ["validate", str(source)])
    assert result.exit_code == 1
    assert "manifest file" in result.stderr
    assert str(source) in result.stderr
    assert "Invalid line" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("kind", ["artifact", "catalogue", "labels", "validator"])
def test_referenced_file_errors_are_printed(tmp_path, monkeypatch, kind):
    validator_module = import_module("kgm.validator")
    monkeypatch.setattr(validator_module, "_ensure_validator", Mock())
    monkeypatch.setattr(
        validator_module.kurra.shacl, "validate", Mock(return_value=(True, Graph(), ""))
    )
    broken = tmp_path / f"broken-{kind}.nt"
    broken.write_text("invalid RDF")
    if kind == "labels":
        broken = Path(__file__).parent / "validator/cs-syntax-error.ttl"
    data = tmp_path / "data.nt"
    graph = Graph()
    graph.add((URIRef("https://example.com/data"), RDF.type, SDO.Dataset))
    graph.serialize(destination=data, format="nt")

    manifest = Graph()
    subject = BNode()
    resource = BNode()
    manifest.add((subject, RDF.type, PREZ.Manifest))
    manifest.add((subject, PROF.hasResource, resource))
    roles = {
        "catalogue": MRR.CatalogueData,
        "labels": MRR.CompleteCatalogueAndResourceLabels,
    }
    manifest.add((resource, PROF.hasRole, roles.get(kind, MRR.ResourceData)))
    manifest.add(
        (
            resource,
            PROF.hasArtifact,
            Literal(str(data) if kind == "validator" else str(broken)),
        )
    )
    if kind == "validator":
        manifest.add((resource, DCTERMS.conformsTo, Literal(broken.name)))
    elif kind == "artifact":
        manifest.add(
            (resource, DCTERMS.conformsTo, URIRef("https://example.com/validator"))
        )
    source = tmp_path / "manifest.nt"
    manifest.serialize(destination=source, format="nt")
    command = (
        ["sync", str(source), "https://example.com/sparql"]
        if kind == "catalogue"
        else ["validate", str(source)]
    )

    result = CliRunner().invoke(app, command)
    assert result.exit_code == 1
    assert str(broken) in result.stderr
    assert ("Bad syntax" if kind == "labels" else "Invalid line") in result.stderr
    assert "Traceback" not in result.stderr
    if kind == "validator":
        assert "validator file" in result.stderr
