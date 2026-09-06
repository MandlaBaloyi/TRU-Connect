import { useQuery } from "@tanstack/react-query";

import { getSupplierProfileProducts } from "../services/supplierSearchService";

/**
 * The category showcase on a supplier's brand profile. Additive to the
 * profile fetch (useSupplierProfile) -- a slow or empty showcase never
 * blocks the header from rendering.
 */
export function useSupplierProfileProducts(supplierId: string) {
  return useQuery({
    queryKey: ["findSupplier", "profileProducts", supplierId] as const,
    queryFn: () => getSupplierProfileProducts(supplierId),
    enabled: Boolean(supplierId),
  });
}
