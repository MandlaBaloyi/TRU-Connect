import type { AddressSuggestion, GeocodedAddress } from "../types";

const latency = (ms = 400) => new Promise<void>((resolve) => setTimeout(resolve, ms));

/**
 * Always returns the same mock-realistic South African address,
 * regardless of the coordinates passed in -- good enough to exercise
 * the picker's UI flow (pin drop -> fields fill in -> edit -> confirm)
 * without a real backend or Mapbox token configured, same reasoning
 * as every other mock service in this feature.
 */
export async function reverseGeocode(_latitude: number, _longitude: number): Promise<GeocodedAddress> {
  await latency();
  return {
    building: null,
    street: "Church Street",
    suburb: "Westenburg",
    city: "Polokwane",
    province: "Limpopo",
    postalCode: "0699",
  };
}

const MOCK_SUGGESTIONS: AddressSuggestion[] = [
  { mapboxId: "mock-1", name: "University Road", fullAddress: "University Road, Mankweng, Limpopo" },
  { mapboxId: "mock-2", name: "Church Street", fullAddress: "Church Street, Westenburg, Polokwane, Limpopo" },
  { mapboxId: "mock-3", name: "Market Street", fullAddress: "Market Street, Seshego, Polokwane, Limpopo" },
];

export async function suggestAddress(query: string, _sessionToken: string): Promise<AddressSuggestion[]> {
  await latency(250);
  if (!query.trim()) return [];
  return MOCK_SUGGESTIONS.filter((s) => s.name.toLowerCase().includes(query.toLowerCase()));
}

export async function retrieveAddress(
  mapboxId: string,
  _sessionToken: string
): Promise<{ latitude: number; longitude: number }> {
  await latency(250);
  // Same mock coordinate regardless of which suggestion was tapped --
  // good enough to exercise "search picks a suggestion, map recenters,
  // fields refill" without needing three distinct fake locations.
  return { latitude: -23.9105, longitude: 29.4547 };
}
