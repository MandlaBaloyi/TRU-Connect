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
 * bulkUpdateStockStatus itself has since been removed entirely from
 * products/api (mock, http, and the switcher) -- it called a
 * stock_status endpoint the real backend never actually built, and
 * had no caller left anywhere in the UI. If a genuine admin-tooling
 * need for bulk stock-status writes ever arises, it should be a new,
 * deliberately-designed endpoint, not a resurrection of this one.
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

import {
  bulkAdjustPrice,
  bulkArchiveProducts,
  bulkDeleteProducts,
  bulkSetDiscount,
  bulkUnarchiveProducts,
} from "../../products/api/productsApi";
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

  const setDiscountMutation = useMutation({
    mutationFn: ({ productIds, discountPercent }: { productIds: string[]; discountPercent: number }) =>
      bulkSetDiscount(productIds, discountPercent),
    onSuccess: invalidateAll,
  });

  const archiveMutation = useMutation({
    mutationFn: (productIds: string[]) => bulkArchiveProducts(productIds),
    onSuccess: invalidateAll,
  });

  const unarchiveMutation = useMutation({
    mutationFn: (productIds: string[]) => bulkUnarchiveProducts(productIds),
    onSuccess: invalidateAll,
  });

  const deleteMutation = useMutation({
    mutationFn: (productIds: string[]) => bulkDeleteProducts(productIds),
    onSuccess: invalidateAll,
  });

  return {
    bulkAdjustPrice: adjustPriceMutation.mutateAsync,
    isBulkAdjustingPrice: adjustPriceMutation.isPending,
    bulkSetDiscount: setDiscountMutation.mutateAsync,
    isBulkSettingDiscount: setDiscountMutation.isPending,
    bulkArchive: archiveMutation.mutateAsync,
    isBulkArchiving: archiveMutation.isPending,
    bulkUnarchive: unarchiveMutation.mutateAsync,
    isBulkUnarchiving: unarchiveMutation.isPending,
    bulkDelete: deleteMutation.mutateAsync,
    isBulkDeleting: deleteMutation.isPending,
  };
}
