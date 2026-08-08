# Library

Once installed in a Python environment, you can import KGM's functions like this:

```python
from kgm.validator import validate
from kgm.labeller import label
from kgm.documentor import table, catalogue
from kgm.loader import load
from kgm.syncer import sync
```

The [manifest guide](guide/manifests.md) introduces the data model. The [API reference](api/index.md) to the left is generated from KGM's 
Python docstrings, so it stays aligned with the installed interfaces.

## Main Functions Overview

The main functions which correspond to Command Line options are:

* **document**
    * **table**: can create a Markdown or ASCIIDOC table of Resources from a KGM file for use in README files
      in repositories
    * **catalogue**: add the IRIs of resources within a Manifest's 'Resource Data' object to a catalogue RDF file
* **label**
    * lists all the IRIs for elements within a Manifest's resources that don't have labels. Given a source of additional
      labels, it can try to extract any
      missing labels and insert them into a Manifest as an additional labelling resource
        *  [KurrawongAI's Semantic Background](guide/manifests.md#semantic-background) is included as a source of labels be default
* **load**
    * creates single RDF dataset files (n-quads) for all resources in a Manifest or uploads them to a SPARQL Endpoint
    * a simpler function that `sync`
* **sync**
    * synchronises resources listed in a Manifest with versions of them in a SPARQL Endpoint
    * acts as `load` if run against an empty SPARQL Endpoint
* **validate**
    * performs SHACL validation on the Manifest, followed by existence checking for each resource - are they reachable
      by this script on the file system or over the Internet? 
    * Will also check any [Conformance Claims](guide/manifests.md#conformance-claims) given in the Manifest
* **event**
    * event-based KGMs actions - for advanced systems use