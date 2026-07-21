/**
 * Reserved integration point for map/location providers.
 * Ref: master prompt "External API Ready > Maps" (Google Maps,
 * OpenStreetMap, Geoapify) -- used for Nearby Suppliers, Business
 * Location, Delivery Radius, Address Verification.
 *
 * Not implemented yet. Nothing in the current dashboards calls this --
 * "Nearby Suppliers" currently comes from GET /suppliers/nearby
 * (docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.3), which the
 * backend is expected to resolve server-side for now. This module
 * exists so a client-side maps provider can be dropped in later without
 * restructuring the business dashboard's data layer.
 */

export type MapsProvider = "google" | "openstreetmap" | "geoapify";

export interface GeoCoordinates {
  latitude: number;
  longitude: number;
}

export async function reverseGeocode(_coords: GeoCoordinates): Promise<never> {
  throw new Error(
    "mapsIntegration.reverseGeocode is not implemented yet -- see docs/08_PRODUCT_ROADMAP.txt"
  );
}

export async function getDeliveryRadius(_origin: GeoCoordinates, _destination: GeoCoordinates): Promise<never> {
  throw new Error(
    "mapsIntegration.getDeliveryRadius is not implemented yet -- see docs/08_PRODUCT_ROADMAP.txt"
  );
}
