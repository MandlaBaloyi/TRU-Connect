/**
 * useProducts — the supplier's whole catalogue, filtered by search
 * term / stock status. Loading / error / empty are separate flags
 * (never blended), same reasoning as Order Book's useOrderBook: "empty
 * because nothing's been listed yet" needs a different screen from
 * "empty because a filter matched nothing". Query is gated on the
 * current user id having loaded, so nothing can fire under the wrong
 * account's cache key.
 */

import { useQuery } from "@tanstack/react-query";

import type { Product, ProductFilters } from "../types";
import { getProducts } from "../api/productsApi";
import { hasFilters, productsKeys } from "./productsKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useProducts(filters?: ProductFilters) {
  const userId = useCurrentUserId();

  const productsQuery = useQuery<Product[]>({
    queryKey: productsKeys.list(userId, filters),
    queryFn: () => getProducts(filters),
    enabled: Boolean(userId),
  });

  const products = productsQuery.data ?? [];
  const productCount = products.length;
  const filtersActive = hasFilters(filters);

  return {
    products,
    productCount,

    isLoading: productsQuery.isLoading,
    isRefreshing: productsQuery.isFetching,
    isError: productsQuery.isError,
    error: productsQuery.error,

    isEmpty: !productsQuery.isLoading && productCount === 0 && !filtersActive,
    isFilteredEmpty: !productsQuery.isLoading && productCount === 0 && filtersActive,

    refetch: productsQuery.refetch,
  };
}
