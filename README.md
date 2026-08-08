![](/docs/assets/logo-kgm.svg)

# KGM

KGM is a tool that performs data management functions for [Knowledge Graphs](https://en.wikipedia.org/wiki/Knowledge_graph) and with [RDF](https://en.wikipedia.org/wiki/Resource_Description_Framework) data files. 
These include synchronising data loaded into KGs with RDF files in directories, obtaining labels for IRIs in KGs and more.

The tool is implemented as a Python command line application and code library which builds on [RDFLib](https://pypi.org/project/rdflib/) and 
[kurra](https://github.com/Kurrawong/kurra).

## Documentation

For Installation, Use and all of KGM's capabilities, see the documentation: https://kurrawong.github.io/kgm/.

## Testing

Run `uv run pytest`, or Poetry etc. equivalents, to execute pytest. You must have Docker Desktop running to allow all
loader tests to be executed as some use temporary test containers.

## Extending

Many functions have been placed into `kgm/utils.py` and hopefully extensions can be made to individual
functions there.

For example, to extend the criteria KGM uses to judge the newness of a local v. a remote artefacts for the
`sync` function, see the [`compare_version_indicators()`](kgm/utils.py#L397)

## License

This code is available for reuse according to the [BSD 3-Clause License](https://opensource.org/license/bsd-3-clause).

&copy; 2024-2026 KurrawongAI

## Contributing

Contributions are welcome through Issues or Pull Requests created in this repository.

## Contact

For all matters, please contact:

**KurrawongAI**  
<info@kurrawong.ai>  
<https://kurrawong.ai>

## Release Procedure

* format code: `task format`
* pass tests: `task test`
* update version in pyproject.toml
* commit all updates: `git commit -a "..."`
* make GitHub release
  * this will trigger pypi.yml workflow to publish to PyPI
* update version in pyproject.toml to next release alpha and push
