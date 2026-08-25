/**
 * useProduct — a single product by id, for ProductDetailScreen. Same
 * user-scoping discipline as useProducts.
 *
 * AUTOMATICALLY POLLS WHILE THIS PRODUCT'S PHOTO MIGHT STILL BE
 * SCANNING -- see pendingPhotoPolling.ts's own docstring for the full
 * reasoning. This is the exact screen real device testing showed
 * stuck on a placeholder box after a photo had already been approved
 * seconds earlier -- nothing was wrong with the data, the screen
 * simply never asked again.
 */

import { useQuery } from "@tanstack/react-query";

import type { Product } from "../types";
import { getProduct } from "../api/productsApi";
import { pollIntervalForProduct } from "./pendingPhotoPolling";
import { productsKeys } from "./productsKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useProduct(productId: string) {
  const userId = useCurrentUserId();

  const query = useQuery<Product>({
    queryKey: productsKeys.detail(userId, productId),
    queryFn: () => getProduct(productId),
    enabled: Boolean(userId) && Boolean(productId),
    refetchInterval: (query) => pollIntervalForProduct(query.state.data),
  });

  return {
    product: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
