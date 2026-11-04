"""Validate a KGM file.

This script performs both SHACL validation to ensure the Manifest is valid according to the KGM
specification (see https://prez.dev/manifest/) and checks that all the resources indicated by the Manifest
- whether local files/folders or remote resources on the Internet - are reachable.

~$ python validate.py {MANIFEST_FILE_PATH}"""

from pathlib import Path

import httpx2
import kurra.shacl
from pyparsing import Literal
from rdflib import BNode, Graph, URIRef
from rdflib.namespace import DCTERMS, PROF, SDO

from kgm.rdf import check_rdf_syntax, load_graph, parsing_source
from kgm.utils import get_background_graph, get_files_from_artifact, resource_is_ignored


class ManifestValidationError(Exception):
    pass


def _ensure_validator(iri: str) -> None:
    """Ask Kurra to cache only the requested validator, if missing."""
    if iri in kurra.shacl.list_local_validators():
        return

    with parsing_source(iri, "validator"):
        validators = kurra.shacl.sync_validators(validator_iris=[iri])
    if iri not in validators:
        raise ManifestValidationError(
            f"The validator <{iri}> indicated in the manifest file is not known to the Semantic Background"
        )


def validate(manifest: Path, rdf: bool = False) -> Graph:
    """Validates a manifest and any assets listed in it with a conformance claim.

    Uses validators known in the Semantic Background or supplied by the user.

    Args:
        manifest: path to a manifest file
        rdf: parse all referenced RDF artifacts using Kurra's reformat --check

    Returns:
        Graph of validated manifest
    """

    if not Path(manifest).is_file():
        raise ManifestValidationError("Manifest file does not exist")

    # can't use get_manifest_paths_and_graph() here as that function uses validate()
    manifest_path = manifest
    manifest_root = Path(manifest).parent.resolve()
    with parsing_source(manifest, "manifest file"):
        manifest_graph = load_graph(manifest)

    ME = Path(__file__)

    def literal_resolves_as_file_folder_or_url(lit: Literal):
        l_str = str(lit)
        if l_str.startswith("http") and "://" in l_str:
            r = httpx2.get(l_str)
            if 200 <= r.status_code < 400:
                pass
            else:
                raise ManifestValidationError(
                    f"Remote content link non-resolving: {l_str}"
                )
        elif any(marker in l_str for marker in "*?["):
            prefix = []
            for part in Path(l_str).parts:
                if any(marker in part for marker in "*?["):
                    break
                prefix.append(part)
            dir = manifest_root / Path(*prefix)
            if not Path(dir).is_dir():
                raise ManifestValidationError(
                    f"The content link {l_str} is not a directory"
                )
        else:
            # It must be a local
            if not (manifest_root / l_str).is_file():
                raise ManifestValidationError(
                    f"Content link {manifest_root / l_str} is invalid - not a file"
                )

    # validate the manifest
    _ensure_validator("https://prez.dev/manifest-validator")

    v = kurra.shacl.validate(
        [manifest_graph, load_graph(ME.parent / "mrr.ttl")],
        "https://prez.dev/manifest-validator",
    )
    if not v[0]:
        raise ManifestValidationError(
            f"The manifest file is invalid ({manifest}):\n\n{v[2]}"
        )

    # get the background graph for merging into artifact graphs for validation
    background_graph = get_background_graph(manifest)

    # validate each resource with a conformance claim
    # Resolve each distinct validator without synchronizing the remote catalogue.
    validators = set()
    for resource in manifest_graph.objects(None, PROF.hasResource):
        if resource_is_ignored(manifest_graph, resource):
            continue
        validators.update(manifest_graph.objects(resource, DCTERMS.conformsTo))
        for artifact in manifest_graph.objects(resource, PROF.hasArtifact):
            validators.update(manifest_graph.objects(artifact, DCTERMS.conformsTo))
    for validator in validators:
        if str(validator).startswith("http"):
            _ensure_validator(str(validator))
        else:
            if not (manifest_root / str(validator)).is_file():
                raise ManifestValidationError(
                    f"The validator {validator} indicated in the manifest file could not be found at {manifest_root / str(validator)}"
                )

    # validate each file referenced in the Manifest
    for s, resource in manifest_graph.subject_objects(PROF.hasResource):
        if resource_is_ignored(manifest_graph, resource):
            continue
        for artifact in manifest_graph.objects(resource, PROF.hasArtifact):
            if isinstance(artifact, BNode):
                content_location = manifest_graph.value(
                    subject=artifact, predicate=SDO.contentLocation
                )
                # main_entity = manifest_graph.value(subject=artifact, predicate=SDO.mainEntity)
            else:
                content_location = artifact

            # ensure the artifact resolves
            literal_resolves_as_file_folder_or_url(content_location)

            # validate each file in the artifact
            for file in get_files_from_artifact(
                (manifest_path, manifest_root, manifest_graph), content_location
            ):
                if rdf:
                    check_rdf_syntax(file)
                # if there is a conformance claim validator for this artifact, use it
                validator = manifest_graph.value(
                    subject=artifact, predicate=DCTERMS.conformsTo
                )

                # if not, check if the resource has one to use
                if validator is None:
                    validator = manifest_graph.value(
                        subject=resource, predicate=DCTERMS.conformsTo
                    )

                if validator is not None:
                    data_graph = load_graph(file)

                    # all validators indicated in the Manifest will have been confirmed known at this point
                    # or are supplied
                    if isinstance(validator, URIRef):
                        pass
                    else:  # must be a local file
                        validator = manifest_root / str(validator)

                    shapes = str(validator)
                    if isinstance(validator, Path):
                        with parsing_source(validator, "validator file"):
                            shapes = load_graph(validator)
                    v = kurra.shacl.validate([data_graph, background_graph], shapes)
                    if not v[0]:
                        raise ManifestValidationError(
                            f"the artifact {manifest_root / file} is invalid according to validator {validator}:\n\n{v[2]}"
                        )

    return manifest_graph
