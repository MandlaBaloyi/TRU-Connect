import { useState } from "react";
import { keepPreviousData, useInfiniteQuery } from "@tanstack/react-query";

import type {
  ProductPage,
  SeeAllControls,
  SupplierPage,
} from "../services/feedDetailService";

/**
 * One hook for all five "see all" screens.
 *
 * useInfiniteQuery RATHER THAN A PAGE COUNTER, because the alternative
 * is state this screen would have to own and get wrong: which pages are
 * loaded, whether a fetch is in flight, what happens when the user
 * pulls to refresh halfway down. React Query already answers all three.
 *
 * THE FETCH IS OFFSET-BASED and the offset is derived from what is
 * already loaded rather than incremented. Incrementing a counter loses
 * track the moment a refresh shortens the list -- a supplier archiving
 * stock, an order being cancelled -- and the screen then asks for page
 * four of a three-page list and shows nothing.
 */
export function useFeedProducts(
  key: string,
  fetchPage: (offset: number, controls?: SeeAllControls) => Promise<ProductPage>
) {
  // THE FILTERS LIVE HERE, NOT IN THE SCREEN, so the query key and the
  // controls cannot disagree about what is currently being shown --
  // the same arrangement useCategoryBrowse uses, because these are the
  // same screen with different data behind it.
  const [controls, setControls] = useState<SeeAllControls>({ sort: "relevance" });

  const query = useInfiniteQuery<ProductPage>({
    queryKey: [
      "community",
      "detail",
      key,
      controls.search ?? null,
      controls.supplier ?? null,
      controls.sort ?? "relevance",
    ],
    queryFn: ({ pageParam }) => fetchPage(pageParam as number, controls),
    initialPageParam: 0,
    getNextPageParam: (last, pages) => {
      if (!last.hasMore) return undefined;
      return pages.reduce((count, page) => count + page.products.length, 0);
    },
    // KEEPS THE LIST ON SCREEN WHILE IT RELOADS, so the control you
    // just tapped does not flash empty underneath your finger.
    placeholderData: keepPreviousData,
  });

  const first = query.data?.pages[0];

  return {
    products: query.data?.pages.flatMap((page) => page.products) ?? [],
    total: first?.total ?? null,
    suppliers: first?.suppliers ?? [],

    controls,
    setSearch: (search: string) =>
      setControls((current) => ({ ...current, search: search || undefined })),
    // TAPPING THE ACTIVE SUPPLIER CLEARS IT -- the way out is the
    // control you can already see.
    toggleSupplier: (supplier: string) =>
      setControls((current) => ({
        ...current,
        supplier: current.supplier === supplier ? null : supplier,
      })),
    setSort: (sort: NonNullable<SeeAllControls["sort"]>) =>
      setControls((current) => ({ ...current, sort })),

    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    isRefetching: query.isRefetching,
    fetchNextPage: query.fetchNextPage,
    hasNextPage: query.hasNextPage,
    isFetchingNextPage: query.isFetchingNextPage,
  };
}

export function useFeedSuppliers(
  key: string,
  fetchPage: (offset: number) => Promise<SupplierPage>
) {
  const query = useInfiniteQuery({
    queryKey: ["community", "detail", key],
    queryFn: ({ pageParam }) => fetchPage(pageParam as number),
    initialPageParam: 0,
    getNextPageParam: (last, pages) => {
      if (!last.hasMore) return undefined;
      return pages.reduce((count, page) => count + page.suppliers.length, 0);
    },
  });

  return {
    suppliers: query.data?.pages.flatMap((page) => page.suppliers) ?? [],
    total: query.data?.pages[0]?.total ?? 0,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    isRefetching: query.isRefetching,
    fetchNextPage: query.fetchNextPage,
    hasNextPage: query.hasNextPage,
    isFetchingNextPage: query.isFetchingNextPage,
  };
}
