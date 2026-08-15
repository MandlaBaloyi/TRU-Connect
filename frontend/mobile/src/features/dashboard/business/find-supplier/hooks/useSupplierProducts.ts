import { useQuery } from "@tanstack/react-query";

import { getSupplierProducts } from "../services/supplierSearchService";

export function useSupplierProducts(supplierId: string) {
  const query = useQuery({
    queryKey: ["findSupplier", "products", supplierId],
    queryFn: () => getSupplierProducts(supplierId),
    enabled: Boolean(supplierId),
  });

  return {
    products: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}
