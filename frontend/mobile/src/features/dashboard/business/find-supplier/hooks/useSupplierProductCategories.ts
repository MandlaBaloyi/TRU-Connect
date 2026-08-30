import { useQuery } from "@tanstack/react-query";

import { getSupplierProductCategories } from "../services/supplierSearchService";

/** Fetched once per supplier, independent of page/sort/filter -- a
 *  supplier's own distinct category set doesn't change just because
 *  the business viewing it turned a page. Real backend fix for a real
 *  bug: this used to be derived client-side from whatever products
 *  happened to be loaded, which broke once results were paginated. */
export function useSupplierProductCategories(supplierId: string) {
  const query = useQuery({
    queryKey: ["findSupplier", "productCategories", supplierId],
    queryFn: () => getSupplierProductCategories(supplierId),
    enabled: Boolean(supplierId),
  });

  return {
    categories: query.data ?? [],
    isLoading: query.isLoading,
  };
}
