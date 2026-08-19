/**
 * useProduct — a single product by id, for ProductDetailScreen. Same
 * user-scoping discipline as useProducts.
 */

import { useQuery } from "@tanstack/react-query";

import type { Product } from "../types";
import { getProduct } from "../api/productsApi";
import { productsKeys } from "./productsKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useProduct(productId: string) {
  const userId = useCurrentUserId();

  const query = useQuery<Product>({
    queryKey: productsKeys.detail(userId, productId),
    queryFn: () => getProduct(productId),
    enabled: Boolean(userId) && Boolean(productId),
  });

  return {
    product: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
