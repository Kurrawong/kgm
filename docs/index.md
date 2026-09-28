# kgm

KGM is a tool that performs data management functions for [Knowledge Graphs](https://en.wikipedia.org/wiki/Knowledge_graph) and with [RDF](https://en.wikipedia.org/wiki/Resource_Description_Framework) data files. 
These include synchronising data loaded into KGs with RDF files in directories, obtaining labels for IRIs in KGs and more.

It uses [manifests](guide/manifests.md) to describe related resources in a file system, such as a Git repository, and
implements functions to perform operations on them.

The tool is implemented as a Python command line application and code library.

!!! note
    kgm is mainly maintained by [kurrawong.ai](https://kurrawong.ai) but is Open Source, so feel free to [contribute](#license-contributing)!

## Install

This Python package is intended to be used as a Python library, called directly from other Python code, or on the
command line on Linux/UNIX-like systems.

Install the command-line application with [uv](https://docs.astral.sh/uv/):

```shell
uv tool install kgm
```

Or install the package in a Python environment:

```shell
pip install kgm
```

### Latest

You can also always install the latest, unstable, release from its version control
repository: <https://github.com/Kurrawong/kgm/>, but we make KGM releases often, so the latest
shouldn't ever be too far ahead of the most recent release.

## Use

### Command Line

Validate a manifest from the command line:

```shell
kgm validate manifest.ttl
```

Use `-h` at any point in the command line hierarchy to get info, e.g. `kgm -h`, `kgm validate -h`.

See the [Command Line Guide](guide/command-line.md) for more info.

### Library

All of KGM's functions available via the [Command Line interface](guide/command-line.md) are available as functions from 
modules within the `kgm` package. 

For example, the function called by the command `kgm label` is at `kgm.labeller.label`.

The API reference to the left lists each module.

See the [Library Guide](guide/library.md) for more info.

### Logging

You can control the verbosity of the command line tool by setting the `KGM_LOG_LEVEL` environment variable to one of
Python's standard logging levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. The default level is `WARNING`.

For example, to see detailed debug output:

```bash
KGM_LOG_LEVEL=DEBUG kgm load file my-manifest.ttl output.trig
```

Or for informational messages:

```bash
KGM_LOG_LEVEL=INFO kgm validate my-manifest.ttl
```

### Case Studies

#### Case Study: Establish

The Indigenous Studies Unit Catalogue is a new catalogue of resources - books, articles, boxes of archived documents -
produced by
the [Indigenous Studies Unit](https://mspgh.unimelb.edu.au/centres-institutes/onemda/research-group/indigenous-studies-unit)
at the [University of Melbourne](https://www.unimelb.edu.au).

The catalogue is available online via an instance of the [Prez](https://prez.dev) system at <https://data.idnau.org/pid/isu-catalogue>
and the content is managed in the GitHub repository <https://github.com/idn-au/isu-catalogue>.

The catalogue container object is constructed as a `schema:DataCatalog` (and also a `dcat:Catalog`, for compatibility
with legacy systems) containing multiple `schema:CreativeWork` instances with subtyping to indicate 'book', 'artwork'
etc.

The source of the catalogue metadata is the static RDF file `_background/catalogue-metadata.ttl` that was made by hand.

The source of the resources' information is the CSV file `_background/datasets.csv` which was created by hand during a
visit to the Indigenous Studies Unit. This CSV information was converted to RDF files in `resources/` using the custom
script `_background/resources_make.py`.

After creation of the catalogue container object's metadata and the primary resource information, KGM was used
to improve the presentation of the data in Prez in the following ways:

1. A manifest files was created
    * based on the example in this repository in `tests/demo-vocabs/manifest.ttl`
    * the example was copy 'n pasted with only minor changes, see `manifest.ttl` in the ISU catalogue repo
    * the initial manifest file was validated with kgm/validator: `kgm validate isu-catalogue/manifest.ttl`
2. A labels file was automatically generated using kgm/labeller
    * using the [KurrawongAI Semantic Background](https://github.com/Kurrawong/semantic-background) as a source of
      labels
    * using the command `kgm label rdf isu-catalogue/manifest.ttl http://demo.dev.kurrawong.ai/sparql > labels.ttl`
    * the file, `labels.ttl` was stored in the ISU Catalogue repo `_background/` folder and indicated in the manifest
      file with the role of _Incomplete Catalogue And Resource Labels_ as it doesn't provide all missing labels
        * note that this storage could have been done automatically using the `kgm label manifest` command
3. IRIs still missing labels were determined
    * using kgm/labeller again with the command `kgm label iris isu-catalogue/manifest.ttl > iris.txt`, all IRIs
      still missing labels were listed
4. Labels for remaining IRIs were manually created
    * there were only 7 important IRIs (as opposed to system objects that don't need labels) that still needed labels.
      These where manually created in the file `_background/labels-manual.ttl`
    * the manual labels file was added to the catalogue's manifest, also with a role of _Incomplete Catalogue And
      Resource Labels_
5. A final missing labels test was performed
    * running `kgm label iris isu-catalogue/manifest.ttl > iris.txt` again indicated no important IRIs were still missing
      labels
6. The catalogue was enhanced
    * `kgm document catalogue isu-catalogue/manifest.ttl` was run to add all the resources of the catalogue to the
      `catalogue.ttl` file
7. The manifest was documented
    * using kgm/documentor, a Markdown table of the manifest's content was created using the command
      `kgm document table isu-catalogue/manifest.ttl`
    * the output of this command - a Markdown table - is visible in the ISU Catalogue repo's README file.
8. The catalogue was prepared for upload
    * `kgm load file isu-catalogue/manifest.ttl isu-catalogue.trig` was run
    * it produced a single _trig_ file `isu-catalogue.trig` containing RDF graphs which was one-time uploaded to the
      database delivering the catalogue
9. The catalogue and repo were synchronised
    * `kgm sync` was then used repeatedly to synchronise updates to the files in version control with the RDF BY read by Prez

#### Case Study: Sync

If I have a manifest locally, I can load it into a remote SPARQL Endpoint like this:

```bash
kgm load sparql {PATH-TO-MANIFEST} {SPARQL-ENDPOINT}
```

Going forward, I don't have to blow away all the content in the SPARQL Endpoint and reload everything whenever I have
content changes, instead I can use the `sync` command.

`sync` compares "version indicators" per artefact, determines which is more recent and then reports on whether the local
artefact should be uploaded, teh remote one downloaded or whether there are new artefacts present locally or remotely.

The `tests/test_sync/` directory in this repository contains a _local_ and a _remote_ manifest and content. Following
the logic in the testing function `tests/test_sync/test_sync.py::test_sync`, if the _remote_ manifest is loaded, as per
`kgm load sparql tests/test_sync/remote/manifest.ttl {SPARQL-ENDPOINT}` and then `sync` is run like this:

```bash
kgm sync tests/test_sync/local/manifest.ttl {SPARQL-ENDPOINT}
```

You will see a report like this:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ artefact                          ┃ Main Entity                   ┃ Direction    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ /../../../artefact4.ttl           │ http://example.com/dataset/4  │ upload       │
│ /../../../artefact5.ttl           │ http://example.com/dataset/5  │ add-remotely │
│ /../../../artefact6.ttl           │ http://example.com/dataset/6  │ download     │
│ /../../../artefact7.ttl           │ http://example.com/dataset/7  │ upload       │
│ /../../../artefact9.ttl           │ http://example.com/dataset/9  │ same         │
│ /../../../artefacts/artefact1.ttl │ http://example.com/dataset/1  │ same         │
│ /../../../artefacts/artefact2.ttl │ http://example.com/dataset/2  │ upload       │
│ /../../../artefacts/artefact3.ttl │ http://example.com/dataset/3  │ upload       │
│ /../../../catalogue.ttl           │ https://example.com/sync-test │ same         │
│ http://example.com/dataset/8      │ http://example.com/dataset/8  │ add-locally  │
└───────────────────────────────────┴───────────────────────────────┴──────────────┘
```

This is telling you, per artefact, what `sync` will do.

* the local copy of `artefact4.ttl` is newer than the remote one, so it wants to "upload"
* the remote location is missing `artefact5.ttl`, so it wants to upload that too
* `artefact9` is the "same" - no action required
* `artefact6.ttl` is newer remotely, it should be downloaded

You can choose to have `sync` carry out all these actions or only some - default is all - by setting the `update_remote`
and so on input parameters. Setting all to `False` will cause `sync` to do nothing and report only what it _would_ do if
they were not set, e.g.:

```bash
kgm sync tests/test_sync/local/manifest.ttl http://localhost:3030/test/ False False False False
```

Other than doing all this "manually" - interactively, on the command line - I might want to use `sync` in Python
application code or cloud _infracode_ scriptin.

For use in Python applications, just import KGM - `uv add kgm` etc. - and use, as per the use of
`sync` in `tests/test_sync/test_sync.py::test_sync`.

For use in _infracode_, note that the `kgm sync` function can return the table above in JSON by setting the
`response format` input parameter, `-f`.

## License & Contributing

Please see KGM's GitHub repository: <https://github.com/kurrawong/kgm>.

## Contact & support

KGM is maintained by:

**KurrawongAI**  
<https://kurrawong.ai>  
<info@kurrawong.ai>
