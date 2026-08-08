/**
 * Business Profile — real backend implementation.
 * NOT WIRED YET — see mockOrderBookApi.ts / mockBusinessProfileApi.ts's
 * sibling docstrings for why every function here throws rather than
 * silently returning fake data. This gets built and wired after the
 * frontend is reviewed, same order as every other feature in this
 * project.
 */

import type {
  BusinessDetails,
  BusinessProfile,
  ContactDetails,
  BusinessLocation,
  OperatingHistoryInfo,
  SupplierInfo,
  TradingDetails,
} from "../types";

function notImplemented(name: string): never {
  throw new Error(
    `httpBusinessProfileApi.${name} is not implemented yet — backend has not been built. ` +
      `Set EXPO_PUBLIC_USE_MOCK_API=true (or leave unset) to use mock data.`
  );
}

export async function getBusinessProfile(): Promise<BusinessProfile> {
  return notImplemented("getBusinessProfile");
}
export async function updateBusinessDetails(_input: Partial<BusinessDetails>): Promise<BusinessProfile> {
  return notImplemented("updateBusinessDetails");
}
export async function updateContactDetails(_input: Partial<ContactDetails>): Promise<BusinessProfile> {
  return notImplemented("updateContactDetails");
}
export async function updateLocation(_input: Partial<BusinessLocation>): Promise<BusinessProfile> {
  return notImplemented("updateLocation");
}
export async function updateTradingDetails(_input: Partial<TradingDetails>): Promise<BusinessProfile> {
  return notImplemented("updateTradingDetails");
}
export async function updateOperatingHistory(_input: Partial<OperatingHistoryInfo>): Promise<BusinessProfile> {
  return notImplemented("updateOperatingHistory");
}
export async function updateSupplierInfo(_input: Partial<SupplierInfo>): Promise<BusinessProfile> {
  return notImplemented("updateSupplierInfo");
}
