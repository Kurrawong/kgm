# Semantic Background

[KurrawongAI](https://kurrawong.ai)'s collection of curated Semantic Web resources, online at:

* <https://github.com/Kurrawong/semantic-background/>

These resources are manages in a GitHub repository but are available in a number of ways:

1. Via SPARQL
   * use the read-only SPARQL Endpoint at <fuseki.dev.kurrawong.ai/semback/sparql> to query all the semantic Background's resources
2. Within kurra
     * the validators stored in the Semantic Background tool can be listed by kurra using `kurra shacl listv` and then used by IRI or ID
     * try `kurra shacl validate -h`
3. Within KGM
     * functions such as `kgm validate` and `kgm label` use resources from the Semantic Background automatically

The online validation too at <https://tools.kurraong.ai/validate> also uses the Semantic Background validators.

An online, browsable, catalogue view of the Semantic Background's contents will be publicly visible soon!