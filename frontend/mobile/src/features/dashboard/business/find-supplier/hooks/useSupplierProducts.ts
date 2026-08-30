import { useQuery } from "@tanstack/react-query";

import { getSupplierProducts } from "../services/supplierSearchService";
import type { SupplierProductsQuery } from "../types";

export function useSupplierProducts(supplierId: string, query: SupplierProductsQuery = {}) {
  const { page, limit, sort, category } = query;
  const result = useQuery({
    // page/sort/category IN THE KEY, not just supplierId -- this is
    // what makes changing any of them trigger a real new fetch rather
    // than silently reusing a cached response for a different page.
    queryKey: ["findSupplier", "products", supplierId, page, limit, sort, category],
    queryFn: () => getSupplierProducts(supplierId, query),
    enabled: Boolean(supplierId),
  });

  return {
    supplierName: result.data?.supplierName ?? null,
    contact: result.data?.contact ?? null,
    products: result.data?.products ?? [],
    page: result.data?.page ?? 1,
    totalPages: result.data?.totalPages ?? 1,
    totalCount: result.data?.totalCount ?? 0,
    isLoading: result.isLoading,
    isError: result.isError,
    refetch: result.refetch,
  };
}
