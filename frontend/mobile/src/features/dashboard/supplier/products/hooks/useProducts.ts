/**
 * useProducts — the supplier's whole catalogue, filtered by search
 * term / stock status. Loading / error / empty are separate flags
 * (never blended), same reasoning as Order Book's useOrderBook: "empty
 * because nothing's been listed yet" needs a different screen from
 * "empty because a filter matched nothing". Query is gated on the
 * current user id having loaded, so nothing can fire under the wrong
 * account's cache key.
 *
 * AUTOMATICALLY POLLS WHILE A RECENTLY UPLOADED PHOTO MIGHT STILL BE
 * SCANNING -- see pendingPhotoPolling.ts's own docstring for the full
 * reasoning. Found during real device testing: without this, a photo
 * that finished scanning and was approved seconds ago just sat there
 * invisible until the supplier happened to manually pull to refresh.
 *
 * isRefreshing IS DELIBERATELY NOT React Query's own isFetching --
 * that flag goes true for EVERY fetch, including this new silent
 * background poll, which would make the pull-to-refresh spinner
 * flicker on its own every few seconds even though nobody pulled
 * anything. Tracked as its own local flag instead, set true only
 * around a genuine user-initiated refetch() call.
 */

import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import type { Product, ProductFilters } from "../types";
import { getProducts } from "../api/productsApi";
import { pollIntervalForProductList } from "./pendingPhotoPolling";
import { hasFilters, productsKeys } from "./productsKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useProducts(filters?: ProductFilters) {
  const userId = useCurrentUserId();
  const [isManualRefreshing, setIsManualRefreshing] = useState(false);

  const productsQuery = useQuery<Product[]>({
    queryKey: productsKeys.list(userId, filters),
    queryFn: () => getProducts(filters),
    enabled: Boolean(userId),
    refetchInterval: (query) => pollIntervalForProductList(query.state.data ?? []),
  });

  const handleManualRefresh = useCallback(async () => {
    setIsManualRefreshing(true);
    try {
      await productsQuery.refetch();
    } finally {
      setIsManualRefreshing(false);
    }
  }, [productsQuery.refetch]);

  const products = productsQuery.data ?? [];
  const productCount = products.length;
  const filtersActive = hasFilters(filters);

  return {
    products,
    productCount,

    isLoading: productsQuery.isLoading,
    isRefreshing: isManualRefreshing,
    isError: productsQuery.isError,
    error: productsQuery.error,

    isEmpty: !productsQuery.isLoading && productCount === 0 && !filtersActive,
    isFilteredEmpty: !productsQuery.isLoading && productCount === 0 && filtersActive,

    refetch: handleManualRefresh,
  };
}
