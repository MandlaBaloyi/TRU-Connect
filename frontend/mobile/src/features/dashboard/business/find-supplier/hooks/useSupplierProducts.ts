import { useQuery } from "@tanstack/react-query";
import { ApiError } from "@/services/api/apiClient";

import { getSupplierProducts } from "../services/supplierSearchService";
import type { SupplierProductsQuery } from "../types";

export function useSupplierProducts(supplierId: string, query: SupplierProductsQuery = {}) {
  const { page, limit, sort, category, search } = query;
  const result = useQuery({
    // page/sort/category IN THE KEY, not just supplierId -- this is
    // what makes changing any of them trigger a real new fetch rather
    // than silently reusing a cached response for a different page.
    queryKey: ["findSupplier", "products", supplierId, page, limit, sort, category, search],
    queryFn: () => getSupplierProducts(supplierId, query),
    enabled: Boolean(supplierId),
  });

  return {
    supplierName: result.data?.supplierName ?? null,
    supplierBusinessImageUrl: result.data?.supplierBusinessImageUrl ?? null,
    supplierVerificationStatus: result.data?.supplierVerificationStatus ?? null,
    contact: result.data?.contact ?? null,
    products: result.data?.products ?? [],
    page: result.data?.page ?? 1,
    totalPages: result.data?.totalPages ?? 1,
    totalCount: result.data?.totalCount ?? 0,
    isLoading: result.isLoading,
    isError: result.isError,
    // WHY IT FAILED, not just that it did. A 404 here is not a broken
    // connection -- it is the verification curtain: this supplier is
    // not currently visible to buyers. Telling a shopkeeper to check
    // their signal when their signal is fine sends them to fix
    // something that is not broken.
    isUnavailable:
      result.error instanceof ApiError && result.error.status === 404,
    refetch: result.refetch,
  };
}
