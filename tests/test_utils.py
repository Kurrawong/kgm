from datetime import datetime
from pathlib import Path

import httpx2
import pytest
from dateutil.parser import parse as date_parse
from kurra.db.gsp import upload
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import PROF, SDO, SKOS, XSD
from typer.testing import CliRunner

import kgm.loader
from kgm.sparql import query
from kgm.utils import (
    VersionIndicatorComparison,
    absolutise_path,
    compare_version_indicators,
    denormalise_artifacts,
    get_artifact_main_entity_iri,
    get_catalogue_iri_from_manifest,
    get_files_from_artifact,
    get_identifier_from_file,
    get_manifest_paths_and_graph,
    get_version_indicators_local,
    get_version_indicators_sparql,
    localise_path,
    make_httpx2_client,
    path_or_url,
    target_contains_this_manifests_catalogue,
    which_is_more_recent,
)
from kgm.validator import ManifestValidationError

runner = CliRunner()

TESTS_DIR = Path(__file__).resolve().parent


def test_path_or_url():
    s1 = "http://example.com"
    assert path_or_url(s1) == s1

    s2 = "/usr/local"
    assert path_or_url(s2) == Path(s2)


def test_localise_path():
    p = Path("/usr/lib/some-file.txt")
    r = Path("/usr/lib")

    x = localise_path(p, r)

    assert x == Path("some-file.txt")

    p = "/usr/lib/some-file.txt"
    r = Path("/usr/lib")

    x = localise_path(p, r)

    assert x == Path("some-file.txt")

    p = "http://example.com/file/one.txt"
    r = Path("/usr/lib")

    x = localise_path(p, r)

    assert x == p


def test_absolutise_path():
    p = Path("some-file.txt")
    r = Path("/usr/lib")

    x = absolutise_path(p, r)

    assert x == Path("/usr/lib/some-file.txt")

    p = "http://example.com/file/one.txt"
    r = Path("/usr/lib")

    x = absolutise_path(p, r)

    assert x == p


def test_get_files_from_artifact():
    MANIFEST = TESTS_DIR / "demo-vocabs" / "manifest.ttl"

    fs = list(get_files_from_artifact(MANIFEST, Literal("vocabs/*.ttl")))

    assert len(fs) == 2
    assert Path(TESTS_DIR / "demo-vocabs" / "vocabs" / "image-test.ttl") in fs
    assert Path(TESTS_DIR / "demo-vocabs" / "vocabs" / "language-test.ttl") in fs


@pytest.mark.parametrize(
    "pattern,expected",
    [
        ("resources/*.nt", {"resources/main.nt"}),
        (
            "resources/**/*.nt",
            {
                "resources/main.nt",
                "resources/group1/child.nt",
                "resources/group1/deep/nested.nt",
            },
        ),
        ("resources/group*/*.nt", {"resources/group1/child.nt"}),
        ("resources/main*.nt", {"resources/main.nt"}),
    ],
)
@pytest.mark.parametrize("absolute", [False, True])
@pytest.mark.parametrize("blank_node", [False, True])
def test_artifact_globs_recurse_only_with_double_star(
    tmp_path, pattern, expected, absolute, blank_node
):
    files = [
        "resources/main.nt",
        "resources/group1/child.nt",
        "resources/group1/deep/nested.nt",
        "resources/notes.txt",
    ]
    for name in files:
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch()
    (tmp_path / "resources/directory.nt").mkdir()
    graph = Graph()
    location = Literal(str(tmp_path / pattern) if absolute else pattern)
    artifact = BNode() if blank_node else location
    if blank_node:
        graph.add((artifact, SDO.contentLocation, location))
    manifest = (tmp_path / "manifest.nt", tmp_path, graph)
    actual = set(get_files_from_artifact(manifest, artifact))
    assert actual == {tmp_path / name for name in expected}


def test_get_identifier_from_file():
    f1 = TESTS_DIR / "demo-vocabs" / "vocabs" / "image-test.ttl"

    i1 = get_identifier_from_file(f1)
    assert i1[0] == URIRef("https://example.com/demo-vocabs/image-test")

    f2 = TESTS_DIR / "utils/main-entity-tests/artifact-unknown-class.ttl"
    i2 = get_identifier_from_file(f2)
    assert i2 is None  # URIRef("https://example.com/dataset/x")


def test_get_manifest_paths_and_graph():
    MANIFEST = TESTS_DIR / "demo-vocabs" / "manifest.ttl"

    extracted_file_path, manifest_root, manifest_graph = get_manifest_paths_and_graph(
        MANIFEST
    )

    assert extracted_file_path == MANIFEST
    assert manifest_root == MANIFEST.parent
    assert len(manifest_graph) == 21

    with pytest.raises(ManifestValidationError):
        extracted_file_path, manifest_root, manifest_graph = (
            get_manifest_paths_and_graph(Path("fake"))
        )


def test_get_catalogue_iri_from_manifest():
    MANIFEST = TESTS_DIR / "demo-vocabs" / "manifest.ttl"

    assert get_catalogue_iri_from_manifest(MANIFEST) == URIRef(
        "https://example.com/demo-vocabs"
    )


def test_target_contains_this_manifests_catalogue(sparql_endpoint):
    MANIFEST = TESTS_DIR / "demo-vocabs" / "manifest.ttl"

    with httpx2.Client() as http_client:
        # positive test
        query(sparql_endpoint, "DROP ALL", http_client=http_client)
        kgm.loader.sync(MANIFEST, sparql_endpoint, None, True, False, True, False)
        assert target_contains_this_manifests_catalogue(MANIFEST, sparql_endpoint)

        # negative test
        query(sparql_endpoint, "DROP ALL", http_client=http_client)
        assert not target_contains_this_manifests_catalogue(MANIFEST, sparql_endpoint)


# TODO add tests
def test_make_httpx2_client():
    pass


def test_get_main_entity_iri_of_artifact():
    MANIFEST = TESTS_DIR / "demo-vocabs" / "manifest-conformance.ttl"

    assert get_artifact_main_entity_iri(
        MANIFEST.parent / "vocabs/image-test.ttl", MANIFEST
    ) == URIRef("https://example.com/demo-vocabs/image-test")

    assert get_artifact_main_entity_iri(
        MANIFEST.parent / "vocabs/language-test.ttl", MANIFEST
    ) == URIRef("https://example.com/demo-vocabs/language-test")

    # specify the class in the manifest
    assert get_artifact_main_entity_iri(
        TESTS_DIR / "utils/main-entity-tests/artifact-unknown-class.ttl",
        TESTS_DIR / "utils/main-entity-tests/manifest-class.ttl",
    ) == URIRef("https://example.com/dataset/x")

    # specify the class in the function
    assert get_artifact_main_entity_iri(
        TESTS_DIR / "utils/main-entity-tests/artifact-unknown-class.ttl",
        TESTS_DIR / "utils/main-entity-tests/manifest-base.ttl",
        atype=URIRef("http://rdfs.org/ns/void#Dataset"),
    ) == URIRef("https://example.com/dataset/x")

    # specify the instance in the manifest
    assert get_artifact_main_entity_iri(
        TESTS_DIR / "utils/main-entity-tests/artifact-unknown-class.ttl",
        TESTS_DIR / "utils/main-entity-tests/manifest-instance.ttl",
    ) == URIRef("https://example.com/dataset/x")

    # specify the instance in the manifest in a different directory
    assert get_artifact_main_entity_iri(
        TESTS_DIR / "utils/main-entity-tests/artifact-unknown-class.ttl",
        TESTS_DIR / "utils/main-entity-tests/sub/manifest-instance.ttl",
    ) == URIRef("https://example.com/dataset/x")

    # specify the instance in the manifest in a different directory 2
    assert get_artifact_main_entity_iri(
        TESTS_DIR / "utils/main-entity-tests/sub/subsub/artifact-unknown-class.ttl",
        TESTS_DIR / "utils/main-entity-tests/sub/manifest-instance.2.ttl",
    ) == URIRef("https://example.com/dataset/x")


def test_duplicate_additional_types_resolve_one_main_entity():
    manifest = TESTS_DIR / "test_sync/local/manifest-dup.ttl"
    manifest_graph = Graph().parse(manifest, format="turtle")
    resource = manifest_graph.value(
        predicate=PROF.hasArtifact, object=Literal("artifact6.ttl")
    )
    assert resource is not None
    # Repeating an identical RDF triple collapses to one value when parsed.
    assert list(manifest_graph.objects(resource, SDO.additionalType)) == [
        SKOS.ConceptScheme
    ]

    artifacts = denormalise_artifacts((manifest, manifest.parent, manifest_graph))
    main_entities = [
        details["main_entity"]
        for artifact, details in artifacts.items()
        if artifact.name == "artifact6.ttl"
    ]
    assert main_entities == [URIRef("http://example.com/dataset/6")]


def test_get_version_indicators_local():
    MANIFEST = TESTS_DIR / "demo-vocabs" / "manifest.ttl"

    vi = {}
    get_version_indicators_local(
        MANIFEST, TESTS_DIR / "demo-vocabs" / "vocabs" / "language-test.ttl", vi
    )

    assert vi["modified_date"] == date_parse("2024-11-21").date()
    assert vi["version_iri"] == "https://example.com/demo-vocabs/language-test/1.0"

    with pytest.raises(ValueError):
        vi = {}
        get_version_indicators_local(
            MANIFEST, TESTS_DIR / "demo-vocabs" / "language-testx.ttl", vi
        )


def test_get_version_indicators_sparql(sparql_endpoint):
    ASSET_PATH = TESTS_DIR / "demo-vocabs" / "vocabs" / "language-test.ttl"
    ASSET_GRAPH_IRI = "https://example.com/demo-vocabs/language-test"

    c = make_httpx2_client()

    upload(sparql_endpoint, ASSET_PATH, ASSET_GRAPH_IRI, False, http_client=c)

    q = """
        SELECT (COUNT(*) AS ?count) 
        WHERE {
          GRAPH <XXX> {
            ?s ?p ?o
          }
        }        
        """.replace("XXX", ASSET_GRAPH_IRI)

    r = query(
        sparql_endpoint,
        q,
        http_client=c,
        return_format="python",
        return_bindings_only=True,
    )

    assert r[0]["count"] == 71

    r = get_version_indicators_sparql(ASSET_GRAPH_IRI, sparql_endpoint, http_client=c)

    assert r["modified_date"] == date_parse("2024-11-21").date()


def test_compare_version_indicators():
    one = {
        "modified_date": date_parse("2024-11-20").date(),
        "version_info": None,
        "version_iri": None,
        "file_size": None,
        "main_entity_iri": None,
    }

    two = {
        "modified_date": date_parse("2024-11-21").date(),
        "version_info": "1.1",
        "version_iri": None,
        "file_size": None,
        "main_entity_iri": None,
    }

    assert compare_version_indicators(one, two) == VersionIndicatorComparison.Second

    three = {
        "modified_date": None,
        "version_info": "1.2.2",
        "version_iri": None,
        "file_size": None,
        "main_entity_iri": None,
    }

    assert compare_version_indicators(two, three) == VersionIndicatorComparison.Second

    four = {
        "modified_date": None,
        "version_info": "1.2.3",
        "version_iri": None,
        "file_size": None,
        "main_entity_iri": None,
    }

    assert compare_version_indicators(three, four) == VersionIndicatorComparison.Second

    five = {
        "modified_date": None,
        "version_info": None,
        "version_iri": "https://example.com/demo-vocabs/language-test/1",
        "file_size": None,
        "main_entity_iri": None,
    }

    six = {
        "modified_date": None,
        "version_info": None,
        "version_iri": "https://example.com/demo-vocabs/language-test/2.0",
        "file_size": None,
        "main_entity_iri": None,
    }

    assert compare_version_indicators(five, six) == VersionIndicatorComparison.Second

    seven = {
        "modified_date": None,
        "version_info": None,
        "version_iri": "https://example.com/demo-vocabs/language-test/2.1",
        "file_size": None,
        "main_entity_iri": None,
    }

    assert compare_version_indicators(six, seven) == VersionIndicatorComparison.Second


@pytest.mark.parametrize(
    "first,second,expected",
    [
        (
            date_parse("2026-05-25").date(),
            Literal("2019", datatype=XSD.gYear),
            VersionIndicatorComparison.First,
        ),
        (
            Literal("2019", datatype=XSD.gYear),
            date_parse("2026-05-25").date(),
            VersionIndicatorComparison.Second,
        ),
        (
            Literal("2026", datatype=XSD.gYear),
            Literal("2019", datatype=XSD.gYear),
            VersionIndicatorComparison.First,
        ),
        (
            Literal("2019", datatype=XSD.gYear),
            Literal("2019", datatype=XSD.gYear),
            VersionIndicatorComparison.Neither,
        ),
        (
            Literal("2019Z", datatype=XSD.gYear),
            date_parse("2019-01-01").date(),
            VersionIndicatorComparison.Neither,
        ),
        (
            Literal("2019+10:00", datatype=XSD.gYear),
            date_parse("2019-05-25").date(),
            VersionIndicatorComparison.Second,
        ),
        (
            Literal("2026-05-25", datatype=XSD.date),
            Literal("2019", datatype=XSD.gYear),
            VersionIndicatorComparison.First,
        ),
        (
            datetime(2026, 5, 25, 12),
            datetime(2026, 5, 25, 18),
            VersionIndicatorComparison.Neither,
        ),
        (
            date_parse("2026-05-25").date(),
            datetime(2026, 5, 26, 12),
            VersionIndicatorComparison.Second,
        ),
        (
            Literal("2026-05-25T12:00:00Z", datatype=XSD.dateTime),
            Literal("2019", datatype=XSD.gYear),
            VersionIndicatorComparison.First,
        ),
    ],
)
def test_compare_version_indicators_modified_date_types(first, second, expected):
    assert (
        compare_version_indicators({"modified_date": first}, {"modified_date": second})
        == expected
    )


def test_which_is_more_recent(sparql_endpoint):
    ARTIFACT_PATH = TESTS_DIR / "demo-vocabs" / "vocabs" / "language-test.ttl"
    ARTIFACT_MAIN_ENTITY = "https://example.com/demo-vocabs/language-test"

    c = make_httpx2_client()

    upload(sparql_endpoint, ARTIFACT_PATH, ARTIFACT_MAIN_ENTITY, False, http_client=c)

    vi = {
        "main_entity": URIRef("https://example.com/demo-vocabs/language-test"),
        "modified_date": datetime.datetime(2025, 2, 28, 0, 0).date(),
        "version_iri": "https://example.com/demo-vocabs/language-test/1.1",
        "file_size": 5053,
    }

    r = which_is_more_recent(vi, sparql_endpoint, http_client=c)

    assert r == VersionIndicatorComparison.First

    vi2 = {
        "main_entity": URIRef("https://example.com/demo-vocabs/language-test"),
        "modified_date": datetime.datetime(2023, 2, 28, 0, 0).date(),
        "file_size": 5053,
    }

    r = which_is_more_recent(vi2, sparql_endpoint, http_client=c)

    assert r == VersionIndicatorComparison.Second


def test_denormalise_artifacts():
    m = TESTS_DIR / "demo-vocabs" / "manifest-conformance.ttl"
    manifest_path, manifest_root, manifest_graph = get_manifest_paths_and_graph(m)
    x = denormalise_artifacts((manifest_path, manifest_root, manifest_graph))
    assert manifest_root / "catalogue.ttl" in x.keys()
    assert manifest_root / "vocabs/image-test.ttl" in x.keys()
    assert manifest_root / "vocabs/language-test.ttl" in x.keys()
    assert (
        "https://raw.githubusercontent.com/RDFLib/prez/refs/heads/main/prez/reference_data/profiles/ogc_records_profile.ttl"
        in x.keys()
    )
    assert manifest_root / "_background/labels.ttl" in x.keys()

    assert x[manifest_root / "vocabs/image-test.ttl"]["file_size"] == 20324

    m = TESTS_DIR / "demo-vocabs" / "manifest-conformance.ttl"
    print(Path(m).resolve())
    manifest_path, manifest_root, manifest_graph = get_manifest_paths_and_graph(m)
    x = denormalise_artifacts(m)
    assert manifest_root / "catalogue.ttl" in x.keys()
    assert manifest_root / "vocabs/image-test.ttl" in x.keys()
    assert manifest_root / "vocabs/language-test.ttl" in x.keys()
    assert (
        "https://raw.githubusercontent.com/RDFLib/prez/refs/heads/main/prez/reference_data/profiles/ogc_records_profile.ttl"
        in x.keys()
    )
    assert manifest_root / "_background/labels.ttl" in x.keys()
