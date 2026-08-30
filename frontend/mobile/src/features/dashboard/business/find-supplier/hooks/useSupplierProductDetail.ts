import { useQuery } from "@tanstack/react-query";

import { getSupplierProduct } from "../services/supplierSearchService";

export function useSupplierProductDetail(supplierId: string, productId: string) {
  const query = useQuery({
    queryKey: ["findSupplier", "product", supplierId, productId],
    queryFn: () => getSupplierProduct(supplierId, productId),
    enabled: Boolean(supplierId) && Boolean(productId),
  });

  return {
    product: query.data ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}
