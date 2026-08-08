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
  Manifest --1:1-N--> Resource;
  Resource --1:1--> artifact;
  Resource --1:1--> role;
  Resource --1:0-1--> name;
  Resource --1:0-1--> decription;
```

The Manifest Model is simply a Manifest class, `prez:Manifest`, which MUST have 1 or more Resource Descriptors, `prof:ResourceDescriptor` indicated by the `prof:hasResource` predicate. 

Each Resource Descriptor MUST have exactly one `prof:hasArtifact` predicate indicating an RDF literal resource (string) giving a file path or path pattern containing the resource information, relative to the manifest.

Each Resource Descriptor MUST also have exactly one `prof:hasRole` predicate indicating a Concept from the _Manifest Resource Roles Vocabulary_.

Each Resource Descriptor MAY have a `schema:name` and/r a `schema:description` predicate indicating literal resources naming and describing it.

### Manifest Resource Roles Vocabulary

This roles vocabulary contains the allowed roles that a resource can play with respect to a Manifest.

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

#### SHACL Validation

This [SHACL](https://www.w3.org/TR/shacl/) validator Shapes Graph file can be used by SHACL validation software such as 
[pySHACL](https://pypi.org/project/pyshacl/), to test the validity of a Manifest's RDF file with respect to this model:

* <https://github.com/Kurrawong/kgm/blob/main/kgm/validator.ttl>

This Shapes Graph is also loaded in to KurrawongAI's Semantic Background and is available via their validator tool 
online and can be selected there for use via the "Use Validators" button:

* <https://tools.kurrawong.ai/validate>

#### KGM validation

Validation beyond just SHACL is needed for an effective manifest as the `manifest.ttl` file necessarily indicates 
other resources that must be present and correct for the whole manifest to work. To validate all aspects of a manifest,
use the in-build KGM command: `kgm validate {PATH-TO-MANIFEST-FILE}`.

This function also validates the contents linked to in the manifest as per their [Conformance Claims](#conformance-claims).

This KGM validation is automatically performed before other KGM commands like `sync`.

#### Conformance Claims

A claim that some data conforms to a standard or a profile. In KGM, this is about indicating that a Resource
is expected to conform to a standard.

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

`kgm validate` will acquire validators indicated in conformance claims, either from KurrawongAI's Semantic Background, or
from a locally-supplied SHACL validator Shapes Graph, and will validate all resources within that manifest resource with
it. In the GA Vocabs above, all vocabulary files in the path `"vocabularies/*.ttl"` will be validated with VocPub.

### Semantic Background

[KurrawongAI](https://kurrawong.ai) makes available about 100 well-known ontologies, 50 or so Shapes GRaph validators
and many vocabularies within its _Semantic Background_, an online reference dataset of RDF content that KGM can
access. this allows KGM to acquire many labels for RDF elements within a manifest's resources and to validate resource
without the user needing to supply anything.

You can see exactly what's in the Semantic Background, which is set up using KGM manifests, here:

* <https://github.com/Kurrawong/semantic-background>