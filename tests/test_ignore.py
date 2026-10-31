from importlib import import_module
from unittest.mock import Mock

import pytest
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import DCTERMS, PROF, RDF, SDO, XSD

from kgm.definednamespaces import MRR, PREZ
from kgm.syncer import get_sync_dataset, sync
from kgm.utils import denormalise_artifacts
from kgm.validator import ManifestValidationError, validate

validator_module = import_module("kgm.validator")


@pytest.fixture
def manifest_with_ignored_resources(tmp_path, monkeypatch):
    graph = Graph()
    manifest = BNode()
    graph.add((manifest, RDF.type, PREZ.Manifest))
    catalogue = URIRef("https://example.com/catalogue")
    catalogue_graph = Graph()
    catalogue_graph.add((catalogue, RDF.type, SDO.DataCatalog))
    catalogue_graph.add((catalogue, SDO.name, Literal("Catalogue")))
    catalogue_graph.serialize(destination=tmp_path / "catalogue.nt", format="nt")
    active = BNode()
    graph.add((manifest, PROF.hasResource, active))
    graph.add((active, PROF.hasRole, MRR.CatalogueData))
    graph.add((active, PROF.hasArtifact, Literal("catalogue.nt")))

    (tmp_path / "invalid.nt").write_text("invalid RDF")
    for role in [MRR.ResourceData, MRR.CompleteCatalogueAndResourceLabels]:
        resource = BNode()
        graph.add((manifest, PROF.hasResource, resource))
        graph.add((resource, PROF.hasRole, role))
        graph.add((resource, PREZ.ignore, Literal(True)))
        graph.add(
            (resource, DCTERMS.conformsTo, URIRef("https://example.com/validator"))
        )
        for location in [
            "missing.nt",
            "invalid.nt",
            "absent/*.nt",
            "https://example.com/data",
        ]:
            graph.add((resource, PROF.hasArtifact, Literal(location)))
        artifact = BNode()
        graph.add((resource, PROF.hasArtifact, artifact))
        graph.add((artifact, SDO.contentLocation, Literal("missing-blank-node.nt")))
        graph.add((artifact, SDO.mainEntity, URIRef("https://example.com/ignored")))
        graph.add((artifact, DCTERMS.conformsTo, Literal("missing-validator.nt")))

    path = tmp_path / "manifest.nt"
    graph.serialize(destination=path, format="nt")
    monkeypatch.setattr(validator_module, "_ensure_validator", Mock())
    monkeypatch.setattr(
        validator_module.kurra.shacl, "validate", Mock(return_value=(True, Graph(), ""))
    )
    monkeypatch.setattr(
        validator_module.httpx,
        "get",
        Mock(side_effect=AssertionError("Ignored URL accessed")),
    )
    return path, graph, catalogue


def test_ignore_skips_artifact_access_and_validator_lookup(
    manifest_with_ignored_resources,
):
    path, graph, _ = manifest_with_ignored_resources
    assert isomorphic(validate(path), graph)
    validator_module._ensure_validator.assert_called_once_with(
        "https://prez.dev/manifest-validator"
    )
    assert list(denormalise_artifacts(path)) == [path.parent / "catalogue.nt"]


def test_ignore_excludes_artifacts_from_export(manifest_with_ignored_resources):
    path, _, catalogue = manifest_with_ignored_resources
    dataset = get_sync_dataset(path)
    assert (catalogue, RDF.type, SDO.DataCatalog) in dataset.graph(catalogue)
    assert not any(dataset.triples((URIRef("https://example.com/ignored"), None, None)))


def test_ignore_prevents_remote_rediscovery(
    monkeypatch, manifest_with_ignored_resources
):
    path, _, _ = manifest_with_ignored_resources
    syncer = import_module("kgm.syncer")
    monkeypatch.setattr(
        syncer,
        "query",
        lambda endpoint, query, **kwargs: (
            False if query.startswith("ASK") else [{"p": "https://example.com/ignored"}]
        ),
    )
    upload = Mock()
    monkeypatch.setattr(syncer, "upload", upload)
    monkeypatch.setattr(syncer, "delete", Mock())
    monkeypatch.setattr(
        syncer, "clear", Mock(side_effect=AssertionError("Ignored labels loaded"))
    )
    monkeypatch.setattr(
        syncer,
        "store_remote_artifact_locally",
        Mock(side_effect=AssertionError("Ignored resource downloaded")),
    )
    status = sync(path, "https://example.com/sparql")
    assert list(status) == [str(path.parent / "catalogue.nt")]
    assert all(call.args[2] != "http://background" for call in upload.call_args_list)


@pytest.mark.parametrize("ignore", [False, None])
def test_false_or_absent_ignore_does_not_skip_validation(tmp_path, monkeypatch, ignore):
    manifest = BNode()
    resource = BNode()
    graph = Graph()
    graph.add((manifest, RDF.type, PREZ.Manifest))
    graph.add((manifest, PROF.hasResource, resource))
    graph.add((resource, PROF.hasRole, MRR.ResourceData))
    graph.add((resource, PROF.hasArtifact, Literal("missing.nt")))
    if ignore is not None:
        graph.add((resource, PREZ.ignore, Literal(ignore)))
    path = tmp_path / "manifest.nt"
    graph.serialize(destination=path, format="nt")
    monkeypatch.setattr(validator_module, "_ensure_validator", Mock())
    monkeypatch.setattr(
        validator_module.kurra.shacl, "validate", Mock(return_value=(True, Graph(), ""))
    )
    with pytest.raises(ManifestValidationError, match="not a file"):
        validate(path)


def test_all_ignored_catalogue_does_not_create_system_entries(
    manifest_with_ignored_resources,
):
    path, graph, _ = manifest_with_ignored_resources
    for resource in graph.objects(None, PROF.hasResource):
        graph.set((resource, PREZ.ignore, Literal("1", datatype=XSD.boolean)))
    dataset = get_sync_dataset((path, path.parent, graph))
    assert len(dataset) == 0
