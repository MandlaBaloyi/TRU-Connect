import { useQuery } from "@tanstack/react-query";

import { getRelatedProducts } from "../services/supplierSearchService";

/** "More from [Supplier]" -- see the real backend's own
 *  list_related_products docstring for the full reasoning: same
 *  supplier, same category, excludes the product being viewed, capped
 *  at 5, genuinely zero or one when that's all that matches. */
export function useRelatedProducts(supplierId: string, productId: string) {
  const query = useQuery({
    queryKey: ["findSupplier", "relatedProducts", supplierId, productId],
    queryFn: () => getRelatedProducts(supplierId, productId),
    enabled: Boolean(supplierId) && Boolean(productId),
  });

  return {
    relatedProducts: query.data ?? [],
    isLoading: query.isLoading,
  };
}
