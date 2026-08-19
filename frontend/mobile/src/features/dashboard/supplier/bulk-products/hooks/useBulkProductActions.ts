/**
 * useBulkProductActions — the selection-mode mutations (Change Price,
 * Archive). Same invalidate-the-whole-feature rule as every other
 * mutation in products/: the list's counts/filters and any open
 * detail screen both need fresh values immediately, and a bulk action
 * touching dozens of rows makes narrower invalidation not worth the
 * complexity.
 *
 * "UPDATE STOCK" WAS REMOVED FROM HERE -- see BulkEditScreen's own
 * docstring for why bulk-setting Product.stockStatus stopped making
 * sense once Products migrated to inventory-derived status.
 * bulkUpdateStockStatus itself still exists in products/api (harmless,
 * unreferenced by any UI now) in case a real backend still wants that
 * general-purpose bulk endpoint for other callers (admin tooling,
 * etc.) -- only this hook's own exposure of it was retired.
 *
 * DATA-LAYER FUNCTIONS STAY OWNED BY products/api, NOT DUPLICATED HERE
 * -- bulk price/archive operations mutate the exact same underlying
 * Product records single-item update/archive do (same "table"), so
 * they belong with the rest of that data layer, the same way a real
 * backend's ProductRepository would hold both single and bulk update
 * methods rather than splitting them across two repositories hitting
 * one table. This hook only orchestrates: it calls products/api's
 * exported bulk functions and owns the mutation/cache-invalidation
 * concern, which IS this feature's job.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { bulkAdjustPrice, bulkArchiveProducts } from "../../products/api/productsApi";
import { productsKeys } from "../../products/hooks";
import type { PriceAdjustment } from "../types";
import { useCurrentUserId } from "./useCurrentUserId";

export function useBulkProductActions() {
  const userId = useCurrentUserId();
  const queryClient = useQueryClient();

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: productsKeys.all(userId) });
  };

  const adjustPriceMutation = useMutation({
    mutationFn: ({ productIds, adjustment }: { productIds: string[]; adjustment: PriceAdjustment }) =>
      bulkAdjustPrice(productIds, adjustment),
    onSuccess: invalidateAll,
  });

  const archiveMutation = useMutation({
    mutationFn: (productIds: string[]) => bulkArchiveProducts(productIds),
    onSuccess: invalidateAll,
  });

  return {
    bulkAdjustPrice: adjustPriceMutation.mutateAsync,
    isBulkAdjustingPrice: adjustPriceMutation.isPending,
    bulkArchive: archiveMutation.mutateAsync,
    isBulkArchiving: archiveMutation.isPending,
  };
}
