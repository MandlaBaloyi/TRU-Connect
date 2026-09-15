import { useInfiniteQuery } from "@tanstack/react-query";

import type { ProductPage, SupplierPage } from "../services/feedDetailService";

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
  fetchPage: (offset: number) => Promise<ProductPage>
) {
  const query = useInfiniteQuery({
    queryKey: ["community", "detail", key],
    queryFn: ({ pageParam }) => fetchPage(pageParam as number),
    initialPageParam: 0,
    getNextPageParam: (last, pages) => {
      if (!last.hasMore) return undefined;
      return pages.reduce((count, page) => count + page.products.length, 0);
    },
  });

  return {
    products: query.data?.pages.flatMap((page) => page.products) ?? [],
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
