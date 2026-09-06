/**
 * The three business-side routes whose screens show an entity's NAME in
 * their top bar, built in one place instead of hand-concatenated at
 * each call site.
 *
 * WHY THIS EXISTS -- the header flash, reported directly: opening a
 * supplier or a product cold showed the layout's static placeholder
 * ("Supplier" / "Stock Catalogue" / "Product") for a beat, then swapped
 * to the real name once the fetch resolved. Every caller ALREADY had
 * that name in hand when it navigated; it was simply being dropped and
 * re-fetched. These helpers carry it through as a route param so the
 * header is correct on its very first frame.
 *
 * This is the same fix, for the same class of bug, that
 * app/(auth)/create-account.tsx documents in its own docstring (point
 * 6): re-reading a value the caller already had is exactly what
 * produced the visible gap there too.
 *
 * THE NAME IS A DISPLAY HINT, NEVER THE SOURCE OF TRUTH. Each screen
 * still fetches its own real data and prefers the fetched value the
 * moment it lands, so a stale, edited, or absent param self-corrects
 * within a frame rather than sticking. Nothing is authorized off it and
 * nothing is persisted from it -- treat it exactly like a placeholder
 * image, not like data.
 *
 * Built as strings (not typed Href objects) because every existing call
 * site in this codebase already pushes template-literal paths with an
 * `as any` cast -- these keep that shape so they drop in without
 * reworking expo-router's typed-routes setup.
 */

/** A supplier's brand profile — /business/find-supplier/<id> */
export function supplierProfileHref(supplierId: string, supplierName?: string | null): string {
  return withName(`/business/find-supplier/${supplierId}`, "supplierName", supplierName);
}

/** A supplier's stock catalogue — /business/find-supplier/products/<id>
 *  `category` pre-filters it ("See all in <category>" from the brand
 *  profile's own showcase strips). */
export function supplierCatalogHref(
  supplierId: string,
  supplierName?: string | null,
  category?: string | null
): string {
  const base = `/business/find-supplier/products/${supplierId}`;
  const withCategory = category ? `${base}?category=${encodeURIComponent(category)}` : base;
  return withName(withCategory, "supplierName", supplierName);
}

/** One product in detail — /business/my-suppliers/<id>/products/<productId>
 *
 *  Carries BOTH names because that screen's top bar shows both: the
 *  supplier's avatar + business name on the first line, the product
 *  name on the second. Passing only the product name would still leave
 *  the identity half of the header flashing. */
export function productDetailHref(
  supplierId: string,
  productId: string,
  productName?: string | null,
  supplierName?: string | null
): string {
  const base = withName(
    `/business/my-suppliers/${supplierId}/products/${productId}`,
    "productName",
    productName
  );
  return withName(base, "supplierName", supplierName);
}

/** Appends `?key=value` (or `&key=value` when the path already has a
 *  query), skipping it entirely when there's no name to pass -- a
 *  caller that genuinely doesn't know the name yet should produce a
 *  clean URL, not `?supplierName=undefined`. */
function withName(path: string, key: string, value?: string | null): string {
  if (!value) return path;
  return `${path}${path.includes("?") ? "&" : "?"}${key}=${encodeURIComponent(value)}`;
}
