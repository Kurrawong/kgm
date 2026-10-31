import pytest
from rdflib import BNode, Dataset, Graph, Literal, URIRef
from rdflib.namespace import PROF, RDF, SDO
from typer.testing import CliRunner

from kgm.cli import app
from kgm.definednamespaces import MRR, PREZ


@pytest.mark.parametrize("suffix,output_format", [(".nq", "nquads"), (".trig", "trig")])
@pytest.mark.parametrize("existing_output", [False, True])
def test_load_file_catalogue_wildcard(
    monkeypatch, tmp_path, suffix, output_format, existing_output
):
    """Exercise wildcard expansion and export without remote manifest validation."""
    catalogues = tmp_path / "resources" / "catalogues"
    catalogues.mkdir(parents=True)
    catalogue = URIRef("https://example.com/catalogue")
    catalogue_graph = Graph()
    catalogue_graph.add((catalogue, RDF.type, SDO.DataCatalog))
    catalogue_graph.add((catalogue, SDO.name, Literal("Catalogue")))
    catalogue_graph.serialize(destination=catalogues / "catalogue.nt", format="nt")

    manifest_graph = Graph()
    manifest = BNode()
    resource = BNode()
    manifest_graph.add((manifest, RDF.type, PREZ.Manifest))
    manifest_graph.add((manifest, PROF.hasResource, resource))
    manifest_graph.add((resource, PROF.hasRole, MRR.CatalogueData))
    manifest_graph.add(
        (resource, PROF.hasArtifact, Literal("resources/catalogues/*.nt"))
    )
    manifest_file = tmp_path / "manifest.nt"
    manifest_graph.serialize(destination=manifest_file, format="nt")
    monkeypatch.setattr("kgm.validate", lambda path: Graph().parse(path, format="nt"))

    output = tmp_path / f"output{suffix}"
    existing_graph = URIRef("https://example.com/existing")
    existing_triple = (existing_graph, SDO.name, Literal("Existing graph"))
    if existing_output:
        dataset = Dataset()
        dataset.graph(existing_graph).add(existing_triple)
        dataset.serialize(destination=output, format=output_format)

    result = CliRunner().invoke(app, ["load", "file", str(manifest_file), str(output)])

    assert result.exit_code == 0, result.exception
    actual = Dataset().parse(output, format=output_format)
    assert set(actual.graph(catalogue)) == set(catalogue_graph)
    if existing_output:
        assert existing_triple in actual.graph(existing_graph)


def test_load_file_rejects_non_quads_format(monkeypatch, tmp_path):
    def unexpected_load(manifest):
        pytest.fail("Unsupported output format should fail before loading a manifest")

    monkeypatch.setattr("kgm.cli.commands.load.get_sync_dataset", unexpected_load)
    output = tmp_path / "output.ttl"
    result = CliRunner().invoke(app, ["load", "file", "manifest.ttl", str(output)])

    assert result.exit_code == 2
    assert "Use .nq for N-Quads or .trig for TriG" in result.output
    assert not output.exists()
