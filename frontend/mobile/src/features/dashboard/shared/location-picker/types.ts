/**
 * dashboard/shared/location-picker -- moved here from
 * business/orders/components/ once the supplier collection-address
 * feature made the second consumer real, not hypothetical: business
 * checkout uses this for a DELIVER order's pin, and a supplier's own
 * "set your collection address" screen uses the exact same
 * MapPickerModal to set THEIR premises. Genuinely shared now, same
 * reasoning shared/notifications/ was promoted under.
 */

/** What the backend's reverse-geocode lookup guesses -- matches
 *  GeocodedAddress on the backend field-for-field. Every field can be
 *  null: a rural/informal pin may have partial or no coverage. */
export interface GeocodedAddress {
  building: string | null;
  street: string | null;
  suburb: string | null;
  city: string | null;
  province: string | null;
  postalCode: string | null;
}

/** One typeahead result from the Search Box companion search -- just
 *  enough to show in a picker list and pass back into retrieveAddress
 *  once tapped. mapboxId is opaque, only ever fed back into
 *  retrieveAddress, never displayed or stored. */
export interface AddressSuggestion {
  mapboxId: string;
  name: string;
  fullAddress: string | null;
}

/** What the business actually confirms -- always business-owned text
 *  (pre-filled from a GeocodedAddress guess, but editable, and Building
 *  is never pre-filled at all since Mapbox has no such field) plus the
 *  pin's REAL coordinates, read straight from the map widget itself,
 *  never from the geocoding lookup. See MapPickerModal's own docstring
 *  for why that distinction matters. */
export interface DeliveryLocation {
  building: string;
  street: string;
  suburb: string;
  city: string;
  province: string;
  postalCode: string;
  latitude: number;
  longitude: number;
}
