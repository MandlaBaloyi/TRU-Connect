import { useState } from "react";
import { keepPreviousData, useInfiniteQuery } from "@tanstack/react-query";

import { browseCategory } from "../services/browseService";
import type { BrowseFilters, BrowseResult, BrowseSort } from "../types";

/**
 * A category browse: the filters, and what they return.
 *
 * useInfiniteQuery, AND THAT IS THE BUG THIS REPLACES. The old hook was
 * a plain useQuery reading one page of 24 and returning `hasMore` that
 * no screen ever read. Food & Grocery holds 253 offers today; 229 of
 * them were unreachable by any gesture. A category screen that cannot
 * reach its own category is not a density problem.
 *
 * THE FILTERS LIVE HERE, NOT IN THE SCREEN, so the query key and the
 * controls cannot disagree about what is currently being shown. Every
 * filter is in the key: changing one is a real fetch, not a cached
 * answer to a different question.
 *
 * placeholderData KEEPS THE LIST ON SCREEN WHILE IT RELOADS. Without it
 * the products vanish on every chip tap and come back a moment later,
 * so the control you just used flashes empty underneath your finger --
 * the same reason Explore's own hook does this.
 *
 * TOTAL AND BRANDS COME OFF THE FIRST PAGE ONLY. The server sends them
 * at offset zero and omits them afterwards, because they cost a query
 * each and do not change as you scroll. Reading them off page zero
 * rather than the last page is what keeps the header steady.
 */
export function useCategoryBrowse(category?: string) {
  const [filters, setFilters] = useState<BrowseFilters>({ sort: "name" });

  const query = useInfiniteQuery<BrowseResult>({
    queryKey: [
      "catalogue",
      "browse",
      category ?? null,
      filters.search ?? null,
      filters.kind ?? null,
      filters.supplier ?? null,
      filters.mineOnly ?? false,
      filters.sort ?? "name",
    ],
    queryFn: ({ pageParam }) =>
      browseCategory({ category, ...filters, offset: pageParam as number }),
    initialPageParam: 0,
    getNextPageParam: (last, pages) => {
      if (!last.hasMore) return undefined;
      return pages.reduce((count, page) => count + page.products.length, 0);
    },
    enabled: Boolean(category || filters.search),
    placeholderData: keepPreviousData,
  });

  const first = query.data?.pages[0];

  return {
    products: query.data?.pages.flatMap((page) => page.products) ?? [],
    total: first?.total ?? null,
    kinds: first?.kinds ?? [],
    suppliers: first?.suppliers ?? [],

    filters,
    setSearch: (search: string) =>
      setFilters((current) => ({ ...current, search: search || undefined })),
    // TAPPING THE ACTIVE CHIP CLEARS IT. A chip row with no way back to
    // "all" is a trap, and a separate "clear" control is a second thing
    // to find when the chip you can already see will do.
    toggleKind: (kind: string) =>
      setFilters((current) => ({
        ...current,
        kind: current.kind === kind ? null : kind,
      })),
    toggleSupplier: (supplier: string) =>
      setFilters((current) => ({
        ...current,
        supplier: current.supplier === supplier ? null : supplier,
      })),
    // TURNING "MY SUPPLIERS" OFF DROPS THE SUPPLIER CHOICE WITH IT.
    // Leaving a single-supplier filter behind after widening the scope
    // is a filter nobody can see, on a row that no longer shows it.
    toggleMine: () =>
      setFilters((current) => ({
        ...current,
        mineOnly: !current.mineOnly,
        supplier: null,
      })),
    setSort: (sort: BrowseSort) => setFilters((current) => ({ ...current, sort })),
    clearFilters: () => setFilters({ sort: filters.sort }),

    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    isRefetching: query.isRefetching,
    fetchNextPage: query.fetchNextPage,
    hasNextPage: query.hasNextPage,
    isFetchingNextPage: query.isFetchingNextPage,
  };
}
