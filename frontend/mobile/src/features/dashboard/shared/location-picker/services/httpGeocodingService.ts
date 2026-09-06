import { apiGet } from "@/services/api/apiClient";

import type { AddressSuggestion, GeocodedAddress } from "../types";

/**
 * Calls the backend's proxy, never Mapbox directly -- the backend
 * holds the geocoding token, this app never does. See
 * src/domains/network/geocoding on the backend for what actually
 * handles this request.
 */
export async function reverseGeocode(latitude: number, longitude: number): Promise<GeocodedAddress> {
  return apiGet<GeocodedAddress>("/geocoding/reverse", { params: { latitude, longitude } });
}

/**
 * Search Box's /suggest step. session_token MUST be the SAME value
 * for every suggest call in one search AND the retrieve call that
 * completes it (see useAddressSearch's own session-token handling) --
 * this is what makes a whole search bill as one session, not one per
 * keystroke. proximity is optional, biases results toward the map's
 * current center for local relevance.
 */
export async function suggestAddress(
  query: string,
  sessionToken: string,
  proximity?: { latitude: number; longitude: number }
): Promise<AddressSuggestion[]> {
  return apiGet<AddressSuggestion[]>("/geocoding/search", {
    params: {
      q: query,
      session_token: sessionToken,
      ...(proximity ? { proximity_lat: proximity.latitude, proximity_lng: proximity.longitude } : {}),
    },
  });
}

/**
 * Search Box's /retrieve step -- resolves a tapped suggestion to real
 * coordinates. Deliberately returns ONLY latitude/longitude, not
 * address text -- once the map recenters here, the EXISTING
 * reverse-geocode flow fills the address fields, same single source
 * of truth regardless of whether the business searched or panned.
 */
export async function retrieveAddress(
  mapboxId: string,
  sessionToken: string
): Promise<{ latitude: number; longitude: number }> {
  return apiGet<{ latitude: number; longitude: number }>("/geocoding/search/retrieve", {
    params: { mapbox_id: mapboxId, session_token: sessionToken },
  });
}
