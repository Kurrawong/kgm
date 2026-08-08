# Command line

The `kgm` application exposes the package's manifest-management functions. Use `-h` at any level to see the available arguments and options.

```shell
kgm -h
```

## Commands

- `validate` validates a manifest and the resources it describes.
- `label` finds missing labels and can return IRIs, RDF, or an updated manifest.
- `document` generates a resource table or catalogue content.
- `load` loads manifest content into a file or SPARQL endpoint.
- `sync` synchronises local resources with a SPARQL endpoint.
- `event` provides event-based synchronisation for advanced integrations.

For example:

```shell
kgm document table manifest.ttl
kgm load file manifest.ttl output.trig
kgm sync manifest.ttl https://example.com/sparql
```


Run `kgm -h` to list commands, which will be something like this:

```bash
Usage: kgm [OPTIONS] COMMAND [ARGS]...

KGM top-level Command Line Interface. Ask for help (-h) for each Command

╭─ Options ────────────────────────────────────────────────────────────────────────╮
│ --version  -v                                                                    │
│ --help     -h        Show this message and exit.                                 │
╰──────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────╮
│ validate  Validate the structure and content of a KGM                  │
│ sync      Synchronize a KGM's resources with loaded copies of them in  │
│           a SPARQL Endpoint                                                      │
│ label     Discover labels missing from data in a in a KGM and patch    │
│           them                                                                   │
│ document  Create documentation from a KGM                              │
│ load      Load a KGM's content into a file or DB                       │
│ event     Event-based KGMs actions                                     │
╰──────────────────────────────────────────────────────────────────────────────────╯
```

Add `-h` to a command or command group for detailed help, so for the `sync` command:

```shell
kgm sync -h
```

> [!NOTE]
> If (when?) KGM runs into problems such as trying to synchronise resources between files and an RDF DB with missmatching version numbers, you can always run [kurra](https://github.com/kurrawong.kurra) commands to directly manage DB resources.
> 
> For example, you can run `kurra db gsp put {FILE} {SPARQL-ENDPOINT} -g {GRAPH-NAME}` to force a replacement of the grapf, `GRAPH-NAME`, in the RDF DB with the contents of the `FILE`.
