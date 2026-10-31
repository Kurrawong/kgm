from importlib import import_module
from unittest.mock import Mock

import httpx2
import pytest
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import PROF, RDF, SDO
from typer.testing import CliRunner

from kgm.cli import app
from kgm.definednamespaces import MRR, PREZ
from kgm.rdf import RDFParseError, check_rdf_syntax
from kgm.utils import denormalise_artifacts
from kgm.validator import validate


@pytest.fixture
def syntax_manifest(tmp_path, monkeypatch):
    validator_module = import_module("kgm.validator")
    monkeypatch.setattr(validator_module, "_ensure_validator", Mock())
    monkeypatch.setattr(
        validator_module.kurra.shacl, "validate", Mock(return_value=(True, Graph(), ""))
    )

    def make_manifest(location, blank=False, ignore=False):
        graph = Graph()
        manifest, resource = BNode(), BNode()
        graph.add((manifest, RDF.type, PREZ.Manifest))
        graph.add((manifest, PROF.hasResource, resource))
        graph.add((resource, PROF.hasRole, MRR.ResourceData))
        if blank:
            artifact = BNode()
            graph.add((artifact, SDO.contentLocation, Literal(location)))
            graph.add((artifact, SDO.mainEntity, URIRef("https://example.com/data")))
        else:
            artifact = Literal(location)
        graph.add((resource, PROF.hasArtifact, artifact))
        if ignore:
            graph.add((resource, PREZ.ignore, Literal(True)))
        path = tmp_path / "manifest.nt"
        graph.serialize(destination=path, format="nt")
        return path

    return make_manifest


@pytest.mark.parametrize("form", ["literal", "blank", "glob"])
def test_rdf_flag_checks_artifacts_without_conformance(tmp_path, syntax_manifest, form):
    folder = tmp_path / "data"
    folder.mkdir()
    broken = folder / "broken.nt"
    broken.write_text("invalid RDF")
    location = "data/*.nt" if form == "glob" else "data/broken.nt"
    manifest = syntax_manifest(location, blank=form == "blank")
    assert validate(manifest)
    with pytest.raises(RDFParseError) as exc_info:
        validate(manifest, rdf=True)
    assert str(broken) in str(exc_info.value)
    assert "Invalid line" in str(exc_info.value)


@pytest.mark.parametrize("flag", ["-r", "--rdf"])
def test_rdf_cli_flag_is_boolean_and_reports_syntax_errors(
    tmp_path, syntax_manifest, flag
):
    broken = tmp_path / "broken.nt"
    broken.write_text("invalid RDF")
    manifest = syntax_manifest(broken.name)
    runner = CliRunner()
    assert runner.invoke(app, ["validate", str(manifest)]).exit_code == 0
    result = runner.invoke(app, ["validate", str(manifest), flag])
    assert result.exit_code == 1
    assert str(broken) in result.stderr
    assert "Invalid line" in result.stderr


def test_reformat_check_preserves_source_and_accepts_formatting_differences(
    tmp_path, monkeypatch, capsys
):
    source = tmp_path / "data.nt"
    content = '<https://example.com/s> <https://example.com/p> "value" .\n'
    source.write_text(content)
    before = source.stat().st_mtime_ns
    rdf_module = import_module("kgm.rdf")
    reformat = Mock(wraps=rdf_module.reformat)
    monkeypatch.setattr(rdf_module, "reformat", reformat)
    check_rdf_syntax(source)
    assert reformat.call_args.kwargs["check"] is True
    assert source.read_text() == content
    assert source.stat().st_mtime_ns == before
    assert list(tmp_path.iterdir()) == [source]
    assert capsys.readouterr().out == ""


def test_rdf_check_skips_ignored_resources(tmp_path, syntax_manifest):
    manifest = syntax_manifest("missing.nt", ignore=True)
    assert validate(manifest, rdf=True)


def test_non_rdf_artifact_is_not_parsed(tmp_path, syntax_manifest):
    source = tmp_path / "document.txt"
    source.write_text("not RDF")
    assert validate(syntax_manifest(source.name), rdf=True)


@pytest.mark.parametrize(
    "suffix,content", [(".nq", "invalid RDF"), (".jsonld", "{broken JSON")]
)
def test_rdf_check_handles_other_rdf_formats(
    tmp_path, syntax_manifest, suffix, content
):
    source = tmp_path / f"broken{suffix}"
    source.write_text(content)
    with pytest.raises(RDFParseError) as exc_info:
        validate(syntax_manifest(source.name), rdf=True)
    assert str(source) in str(exc_info.value)


@pytest.mark.parametrize(
    "url", ["https://example.com/broken.nt", "https://example.com/data"]
)
def test_remote_rdf_errors_identify_url(monkeypatch, url):
    rdf_module = import_module("kgm.rdf")
    response = httpx2.Response(
        200,
        content=b"invalid RDF",
        headers={"content-type": "application/n-triples"},
        request=httpx2.Request("GET", url),
    )
    monkeypatch.setattr(rdf_module.httpx2, "get", Mock(return_value=response))
    with pytest.raises(RDFParseError) as exc_info:
        check_rdf_syntax(url)
    assert url in str(exc_info.value)
    assert "Invalid line" in str(exc_info.value)


@pytest.mark.parametrize("pattern", ["data/*.nt", "data/good*.nt"])
def test_non_recursive_glob_does_not_validate_or_load_nested_files(
    tmp_path, syntax_manifest, pattern
):
    data = tmp_path / "data"
    nested = data / "nested"
    nested.mkdir(parents=True)
    good = data / "good.nt"
    good.write_text(
        "<https://example.com/data> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://schema.org/Dataset> .\n"
    )
    broken = nested / "broken.nt"
    broken.write_text("invalid RDF")

    manifest = syntax_manifest(pattern)
    assert validate(manifest, rdf=True)
    assert set(denormalise_artifacts(manifest)) == {good}

    manifest = syntax_manifest("data/**/*.nt")
    with pytest.raises(RDFParseError) as exc_info:
        validate(manifest, rdf=True)
    assert str(broken) in str(exc_info.value)
