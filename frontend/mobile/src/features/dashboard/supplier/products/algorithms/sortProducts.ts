/**
 * sortProducts — applied on top of whatever the current filter/search
 * already narrowed the list to, never a replacement for either. Never
 * mutates its input (returns a new array), same discipline as every
 * other algorithm in this app.
 *
 * STOCK_FIRST now needs inventoryStatusByProductId -- Product's own
 * stockStatus field is legacy/frozen (see types.ts's own docstring on
 * it), so sorting by IT would silently sort by stale data instead of
 * what the badge on screen actually shows. The caller (ProductsScreen)
 * already has this map for ProductCard's own badge; passed through
 * here rather than this function fetching it independently.
 */

import type { Product, SortOption } from "../types";
import type { InventoryStatus } from "../../inventory/types";

export function sortProducts(
  products: Product[],
  option: SortOption,
  inventoryStatusByProductId?: Map<string, InventoryStatus>
): Product[] {
  const copy = [...products];

  switch (option) {
    case "NAME_ASC":
      return copy.sort((a, b) => a.name.localeCompare(b.name));
    case "PRICE_ASC":
      return copy.sort((a, b) => a.priceCents - b.priceCents);
    case "PRICE_DESC":
      return copy.sort((a, b) => b.priceCents - a.priceCents);
    case "STOCK_FIRST": {
      // Stable sort: each status group keeps its existing relative
      // order -- only the groups get reordered relative to each
      // other. Unknown status (map not loaded yet) sorts last, never
      // assumed in-stock.
      const rank: Record<InventoryStatus | "UNKNOWN", number> = {
        IN_STOCK: 0,
        LOW_STOCK: 1,
        OUT_OF_STOCK: 2,
        UNKNOWN: 3,
      };
      return copy.sort((a, b) => {
        const statusA = inventoryStatusByProductId?.get(a.id) ?? "UNKNOWN";
        const statusB = inventoryStatusByProductId?.get(b.id) ?? "UNKNOWN";
        return rank[statusA] - rank[statusB];
      });
    }
    case "NEWEST":
    default:
      // Already the API's own default ordering -- no-op, not a
      // special case, just nothing further to do.
      return copy;
  }
}
