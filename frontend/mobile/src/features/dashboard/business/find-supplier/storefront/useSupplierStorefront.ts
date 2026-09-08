import { useQuery } from "@tanstack/react-query";

import { apiGet } from "@/services/api/apiClient";
import { USE_MOCK_API } from "@/constants/config";

import { MOCK_SUPPLIER_STOREFRONT } from "./mockSupplierStorefront";
import { MIN_ITEMS_PER_STOREFRONT_SECTION, type StorefrontSection, type SupplierStorefront } from "./types";

/**
 * A supplier's merchandised storefront sections.
 *
 * NOW REAL. All six are served by
 * GET /supplier-discovery/suppliers/{id}/storefront, built from the
 * supplier's own configuration:
 *
 *   ON_SALE      -- compare_at genuinely ABOVE the price, deepest
 *                   discount fraction first.
 *   BEST_SELLERS -- units actually sold, CONFIRMED orders only.
 *   NEW_ARRIVALS -- added within a 45-day window, not merely sorted.
 *   BULK_VALUE   -- unit_quantity > 1, cheapest per unit first.
 *   FEATURED_PRODUCT / CURATED -- the supplier's own picks.
 *
 * THE MOCK IS KEPT, and now honours USE_MOCK_API like every other
 * service rather than being forced on. It has a real job still: the
 * computed sections only appear once a supplier's catalogue actually
 * HAS discounts, sales history and pack sizes in it, so a thin dev
 * database shows two sections where the mock shows six. Designing
 * against the mock and verifying against the API is the point of
 * having both.
 *
 * EXPECT FEWER SECTIONS AGAINST REAL DATA, and that is correct rather
 * than broken -- see the backend service on why a section with under
 * three products removes itself.
 */
async function getSupplierStorefront(supplierId: string): Promise<SupplierStorefront> {
  if (USE_MOCK_API) {
    // A real delay so the "renders nothing while loading" path is
    // exercised rather than skipped by an instant resolve.
    await new Promise((resolve) => setTimeout(resolve, 350));
    return MOCK_SUPPLIER_STOREFRONT;
  }
  return apiGet<SupplierStorefront>(`/supplier-discovery/suppliers/${supplierId}/storefront`);
}

/** Same thin-section rule as the Community feed: a strip with almost
 *  nothing in it reads as broken rather than short. A featured product
 *  is exempt -- it is one item by definition. */
function isWorthRendering(section: StorefrontSection): boolean {
  switch (section.type) {
    case "FEATURED_PRODUCT":
      return true;
    case "ON_SALE":
    case "BEST_SELLERS":
    case "BULK_VALUE":
    case "NEW_ARRIVALS":
    case "CURATED":
      return section.products.length >= MIN_ITEMS_PER_STOREFRONT_SECTION;
    default:
      return false;
  }
}

export function useSupplierStorefront(supplierId: string) {
  const query = useQuery({
    queryKey: ["findSupplier", "storefront", supplierId],
    queryFn: () => getSupplierStorefront(supplierId),
    enabled: Boolean(supplierId),
  });

  return {
    sections: (query.data?.sections ?? []).filter(isWorthRendering),
    isLoading: query.isLoading,
  };
}
