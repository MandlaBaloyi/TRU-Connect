/**
 * Reserved integration point for dedicated search infrastructure.
 * Ref: master prompt "External API Ready > Search" (Algolia,
 * Meilisearch, ElasticSearch) -- Supplier Search, Product Search,
 * Catalogue Search.
 *
 * Not implemented yet. Search today goes through the backend's own
 * GET /suppliers and GET /products endpoints (docs/05, Sections 5.3-5.4).
 * This module is where a dedicated search-as-a-service provider would be
 * wired in later, once fuzzy/ranked search outgrows what the primary
 * database can do efficiently.
 */

export interface SearchResult<T> {
  item: T;
  relevanceScore: number;
}

export async function fuzzySearch<T>(_query: string): Promise<SearchResult<T>[]> {
  throw new Error(
    "searchIntegration.fuzzySearch is not implemented yet -- see docs/08_PRODUCT_ROADMAP.txt"
  );
}
