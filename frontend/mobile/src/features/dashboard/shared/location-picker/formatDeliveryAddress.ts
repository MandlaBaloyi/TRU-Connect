import type { DeliveryLocation } from "./types";

/**
 * Assembles the structured fields into one display string -- fed into
 * delivery_address_text so every existing screen/notification that
 * already reads that single field keeps working unchanged, even
 * though the real, structured data now also lives in its own columns.
 * Empty parts are skipped rather than shown as blank segments (e.g. no
 * "Building" typed -> no leading ", " left dangling).
 */
export function formatDeliveryAddress(location: DeliveryLocation): string {
  return [location.building, location.street, location.suburb, location.city, location.province, location.postalCode]
    .map((part) => part.trim())
    .filter((part) => part.length > 0)
    .join(", ");
}
