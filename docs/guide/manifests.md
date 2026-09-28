# Manifests

A KGM Manifest is an RDF file that describes a related set of resources. Resources may be local files, glob patterns, 
or remote artefacts. Each resource is assigned a role that tells KGM how to handle it.

## Example

```turtle
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX mrr: <https://prez.dev/ManifestResourceRoles/>
PREFIX prez: <https://prez.dev/>
PREFIX prof: <http://www.w3.org/ns/dx/prof/>
PREFIX schema: <https://schema.org/>

[]
    a prez:Manifest ;
    prof:hasResource
        [
            prof:hasArtifact "catalogue.ttl" ;
            prof:hasRole mrr:CatalogueData ;
            schema:name "Catalogue definition" ;
        ] ,
        [
            prof:hasArtifact "vocabularies/*.ttl" ;
            prof:hasRole mrr:ResourceData ;
            schema:name "Resource data" ;
            dcterms:conformsTo <https://linked.data.gov.au/def/vocpub/validator> ;
        ] ,
        [
            prof:hasArtifact "labels.ttl" ;
            prof:hasRole mrr:CompleteCatalogueAndResourceLabels ;
            schema:name "Labels" ;
        ] ;
.
```

In the file above, a catalogue is defined in the file `catalogue.ttl`, a number of vocabularies are in Turtle files in
the folder `vocabularies/`. These are expected to be listed in the catalogue. Complete labels for all the catalogue and
vocabularies content is stored in a `labels.ttl` file.

The complete Prez Manifest model is available at <https://prez.dev/manifest/>.

## Tasks

Things that you can do with manifests:

- **validation** — check the manifest structure, resource availability, and declared SHACL conformance of resources
- **synchronisation** — synchronise the content in a Knowledge Graph - RDF database - up-to-date with RDF files
- **labelling** — find IRIs without labels and add labels from given contexts
- **documentation** — generate human-readable tables and catalogue entries from resources in files

You can perform these tasks using KGM either as a Python library or as a command line application. For example, to 
validate a manifest:

```shell
kgm validate manifest.ttl
```

## Manifest Data Model

``` mermaid
graph LR
  style Manifest fill:#FF90BB,stroke:#666,stroke-width:2px
  Manifest --1:1-N--> ResourceDescriptor;
  style ResourceDescriptor fill:#FFC1DA,stroke:#666,stroke-width:2px
  style artifact fill:#F8F8E1,stroke:#666,stroke-width:2px 
  ResourceDescriptor --1:1-N--> artifact;
  ResourceDescriptor --1:1--> hasRole;
  ResourceDescriptor --1:0-N--> conformsTo;
  ResourceDescriptor --1:0-1--> additionalType;
  ResourceDescriptor --1:0-1--> sync;
  style artifact fill:#F8F8E1,stroke:#666,stroke-width:2px  
  artifact --1:0-N--> conformsTo;
  artifact --1:0-1--> additionalType;
  artifact --1:0-1--> sync;
  artifact --1:0-1--> mainEntity;
  artifact --1:0-1--> contentLocation;
  style artifact fill:#F8F8E1,stroke:#666,stroke-width:2px  
  artifact --1:0-1--> dateModified;
  artifact --1:0-1--> versionIRI;
  artifact --1:0-1--> version;
```

### Model Rules

1. An instance of the Manifest class, `prez:Manifest`, MUST have 1 or more Resource Descriptors, `prof:ResourceDescriptor` instances, indicated by the `prof:hasResource` predicate. The Manifest instance can be identified by an IRI or a Blank Node.

2. Each Resource Descriptor MUST have at least one `prof:hasArtifact` predicate indicating either an RDF literal resource (a string) containing location of the artifact or a Blank Node containing the location of the artifact indicated by the `schema:contentLocation` predicate and the IRI of the main entity within the artifact indicated by `schema:mainEntity`.
    * See the [Main Entity](#main-entity) details below

3. Where content location is indicated, it MUST be a file path or path pattern relative to the manifest file's location, or a URL.

4. Each Resource Descriptor MUST also have exactly one `prof:hasRole` predicate indicating a Concept from the [Manifest Resource Roles Vocabulary](#manifest-resource-roles-vocabulary).

5. Each Resource Descriptor MAY have a `schema:name` and/or a `schema:description` predicate indicating literal resources naming and describing it.

6. A Resource, or an Artifact, MAY indicate that it (if an Artifact) or the Artifacts within it (if a Resource) conform to any number of defined Standards or Profiles of Standards, using the predicate `dcterms:conformsTo`.
    * Validators can be indicated either by using "well known" validator IRIs or by directly indicating a path to a validator RDF file
      * current "well known" are listed below and can be indicated using an IRI like this:
      * `dcterms:conformsTo <WELL-KNONW-VALIDATOR-IRI> ;`
      * other validators, such as `my-local-validator.ttl` or `http://online-validator.com/val.ttl` should be indicated using a literal, like this:
      * `dcterms:conformsTo "path/from/manifest/root/to/my-local-validator.ttl" ;`
    * See the [Known Validators](#known-validators) list below

7. A Resource, or an Artifact, MAY indicate that it (if an Artifact) or the Artifacts within it (if a Resource) is of a specific class, using the predicate `schema:additionalType`
    * See the [Known Classes](#known-classes) list below
8. A Resource, or an Artifact, MAY indicate that it should not be ignored by synchronisation tooling by setting a predicate `prez:sync` to `false`
    * See the [Indicating no action](#indicating-no-action) section below
9. An Artifact may have "versioning information" about it indicated by use of a number of known versioning predicates
    * see the [Artifact Versioning](#artifact-versioning) section below

### Manifest Resource Roles Vocabulary

This roles vocabulary contains the allowed roles that a resource, descrip can play with respect to a Manifest.

The IRI of this vocabulary is:

* `https://prez.dev/ManifestResourceRoles`
    * the vocab namespace is `https://prez.dev/ManifestResourceRoles/`
    * recommended namespace prefix is `mrr`

Human-readable form:

| Concept IRI                               | Label                                   | Definition                                                                                                          | Parent                         |
|-------------------------------------------|-----------------------------------------|---------------------------------------------------------------------------------------------------------------------|--------------------------------|
| `mrr:ContainerData`                       | Container Data                          | Data for the container, usually a Catalogue, including the identity of it and each item fo content                  | -                              |
| `mrr:ContentData`                         | Content Data                            | Data for the content of the container                                                                               | -                              |
| `mrr:ContainerAndContentModel`            | Container & Content Model               | The default model for the container and the content. Must be a set of SAHCL Shapes                                  | -                              |
| `mrr:ContainerModel`                      | Container Model                         | The default model for the container. Must be a set of SAHCL Shapes                                                  | `mrr:containerAndContentModel` |
| `mrr:ContentModel`                        | Content Model                           | The default model for the content. Must be a set of SAHCL Shapes                                                    | `mrr:containerAndContentModel` |
| `mrr:CompleteContainerAndContentLabels`   | Complete Content and Container Labels   | All the labels - possibly indluding names, descriptions & seeAlso links - for the Container and Content objects     | -                              |
| `mrr:IncompleteContainerAndContentLabels` | Incomplete Content and Container Labels | Some of the labels - possibly indluding names, descriptions & seeAlso links - for the Container and Content objects | -                              |

* <https://github.com/Kurrawong/kgm/blob/main/kgm/mrr.ttl>

### Validation

#### Conformance Claims

A claim that some data conforms to a standard or a profile. In KGM, this is about indicating that a Resource
is expected to conform to a standard using the `dcterms:conformsTo` predicate.

In the [Geoscience Australia Vocabs' manifest](https://github.com/GeoscienceAustralia/ga-vocabs/blob/master/manifest.ttl),
there is a conformance claim for the vocabs to the [VocPub Profile's Validator](https://linked.data.gov.au/def/vocpub/validator)
which looks like this:

```turtle
#...
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX mrr: <https://prez.dev/ManifestResourceRoles/>
PREFIX prof: <http://www.w3.org/ns/dx/prof/>
        
[
    prof:hasArtifact "vocabularies/*.ttl" ;
    prof:hasRole mrr:ResourceData ;
    dcterms:conformsTo <https://linked.data.gov.au/def/vocpub/validator> ;
] .
#...
```

`kgm validate` will acquire validators indicated in conformance claims, either from KurrawongAI's [Known Validators](#known-validators), or
from a locally-supplied SHACL validator Shapes Graph, and will validate all resources within that manifest resource with
it. In the GA Vocabs above, all vocabulary files in the path `"vocabularies/*.ttl"` will be validated with VocPub.

#### Known Validators

KurrawongAI maintains a list of [SHACL]([SHACL](https://www.w3.org/TR/shacl/)) Shapes Graphs in our [Semantic Background](semantic-background.md) that can be access by ID within the _kurra_ and _kgm_ tools for Conformance Claims: see point 6. above.

The validators are listed in Validators Catalogue at https://github.com/Kurrawong/semantic-background/blob/main/resources/validators/catalogue.ttl, at within the "Use Validators" function of the https://tools.kurrawong.ai/validate tool and also by typing `kurra shacl listv` on the Command Line using kurra.

There are already 50+ validators there.

#### Manifest Validator

Manifest files themselves can be validated using the KGM manifest validator at:

* <https://github.com/Kurrawong/kgm/blob/main/kgm/validator.ttl>

#### KGM Validation

Validation beyond just SHACL is needed for an effective manifest as the `manifest.ttl` file necessarily indicates 
other resources that must be present and correct for the whole manifest to work. To validate all aspects of a manifest,
use the in-build KGM command: `kgm validate {PATH-TO-MANIFEST-FILE}`.

This function also validates the contents linked to in the manifest as per their [Conformance Claims](#conformance-claims).

This KGM validation is automatically performed before other KGM commands like `sync`.


### Known Classes

Some classes of resource are commonly used in Manifests so these classea are 'built in' and do not need to be indicated within a Manifest. These classes are:

* `dcat:Resource`
* `dcat:Dataset`
* `dcat:Catalog`
* `owl:Ontology`
* `schema:CreativeWork`
* `schema:Dataset`
* `schema:DataCatalog`
* `skos:ConceptScheme`

If an Artifact, or all the Artifacts within a Resource, are not one of these types, then extra types can be indicated as being so by use of `schema:additionalType` like this:

```turtle
[]
    a prez:Manifest ;
    prof:hasResource
        # ...
        [
            prof:hasArtifact "resources/*.ttl" ;
            prof:hasRole mrr:ResourceData ;
            schema:additionalType <{A-CLASS-IRI}> ;
        ] ,
        # ...
.
```

This will allow the Manifest to communicate the class of the object software should be looking for within the resource.

Resources can also be indicated directly, regardless of type, see next section.

### Main Entity

If, for some reason, a resource is neither of one of the Known Classes nore it its class able to be indicated with `schema:additionalType`, the specific IRI of the resource can be indicated using `schema:mainEntity`. This may be needed in situations where an RDF file containing a resource also contains multiple other instance of the same class.

```turtle
[]
    a prez:Manifest ;
    prof:hasResource
        # ...
        [
            prof:hasArtifact "resources/file1.ttl" ;
            prof:hasRole mrr:ResourceData ;
            schema:mainEntity <{RESOURCE-IRI}> ;
        ] ,
        # ...
.
```

### Indicating no action

If a Manifest wishes to list a resource but indicate it not for automatic handling by manifest tooling - perhaps it's too large to synchronise with an RDF DB - then the predicate `prez:sync` with the value `false` should be set.

Here is an example of a Manifest indicating 4 spatial datasets, one of which is too large to sync:

```turtle
[]
    a prez:Manifest ;
    prof:hasResource
        [
            prof:hasArtifact "resources/*.ttl" ;  # datset1.ttl, dataset2.ttl & dataset3.ttl
            prof:hasRole mrr:ResourceData ;
        ] ,
        [
            prof:hasArtifact "resources/large/dataset4.ttl" ;
            prof:hasRole mrr:ResourceData ;
            prez:sync false ;
        ] ;
.        
```

### Artifact versioning

An Artifact's version may be indicated by use of any or all of the following predicates:

* `owl:versionIRI`
* `schema:version` or `owl:versionInfo`
* `schema:dateModified` or `dcterms:modified`

If this is done, then tools, such as _kgmanifest_ that load and sync Manifest-described data, can obtain versioning information from a Manifest file, rather than by inspecting Artifacts' contents.


## Examples

### Valid

A very simple valid Manifest listing a catalogue, vocabularies and a labels file:

```turtle
--8<-- "docs/assets/manifest.ttl"
```

### Invalid - no role

The example above but now invalid as no role is indicated for the vocabs resource:

```turtle
--8<-- "docs/assets/manifest-invalid-01.ttl"
```

If you run `kgm validate path/to/manifest.ttl` on this Manifest file, you will get an error reported.

### Invalid - location

The valid example above but now invalid as the path to `catalogue.ttl` is broken:

```turtle
--8<-- "docs/assets/manifest-invalid-02.ttl"
```

If you run `kgm validate path/to/manifest.ttl` on this Manifest file, if it was real, you would get an error reported.

### `mainEntity` use

A snippet of a Manifest - just one value for resource - showing use of `schema:mainEntity` and `schema:contentLocation` instead of just a literal file path:

```turtle
   [
        prof:hasArtifact
            [
                schema:contentLocation "vocabs/image-test.ttl" ;
                schema:mainEntity <https://example.com/demo-vocabs/image-test> ;
            ] ,
            "vocabs/language-test.ttl" ;
        prof:hasRole mrr:ResourceData ;
    ] ,
```

### conformance claim - one

A single artifact claiming conformance to the [VocPub Profile of SKOS](https://linked.data.gov.au/def/vocpub/spec):

```turtle
    prof:hasArtifact
        [
            schema:contentLocation "vocabs/image-test.ttl" ;
            schema:mainEntity <https://example.com/demo-vocabs/image-test> ;
            dcterms:conformsTo <https://linked.data.gov.au/def/vocpub/validator> ;
        ] ,
```

### conformance claim - all

A single Resource in a Manifest claiming conformance to the VocPub Profile of SKOS for all its artifacts - whatever files are in `vocabs/*.ttl`:

```turtle
    [
        prof:hasArtifact "vocabs/*.ttl" ;
        prof:hasRole mrr:ResourceData ;
        # ...
        dcterms:conformsTo <https://linked.data.gov.au/def/vocpub/validator> ;
    ] ,
```