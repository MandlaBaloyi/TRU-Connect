/**
 * Business Profile — real backend implementation.
 *
 * NO DTO MAPPING LAYER, unlike Order Book/Loan Book's http*Api.ts
 * files — this domain has no money fields (no cents-to-rands
 * conversion needed) and the backend's response shape was built to
 * match this feature's types.ts field-for-field on purpose (see
 * backend BusinessProfileService._to_dict). What comes back over the
 * wire IS a BusinessProfile already; passed straight through rather
 * than re-mapped, since there's genuinely nothing to translate.
 *
 * ONE PATCH ROUTE PER SECTION, matching useBusinessProfileMutations
 * exactly — each function here hits its own dedicated endpoint with a
 * partial body, never one big "save everything" call.
 */

import { apiGet, apiPatch } from "@/services/api/apiClient";
import type {
  BusinessDetails,
  BusinessProfile,
  ContactDetails,
  BusinessLocation,
  OperatingHistoryInfo,
  SupplierInfo,
  TradingDetails,
} from "../types";

export async function getBusinessProfile(): Promise<BusinessProfile> {
  return apiGet<BusinessProfile>("/business-profile");
}

export async function updateBusinessDetails(input: Partial<BusinessDetails>): Promise<BusinessProfile> {
  return apiPatch<BusinessProfile>("/business-profile/business-details", input);
}

export async function updateContactDetails(input: Partial<ContactDetails>): Promise<BusinessProfile> {
  return apiPatch<BusinessProfile>("/business-profile/contact-details", input);
}

export async function updateLocation(input: Partial<BusinessLocation>): Promise<BusinessProfile> {
  return apiPatch<BusinessProfile>("/business-profile/location", input);
}

export async function updateTradingDetails(input: Partial<TradingDetails>): Promise<BusinessProfile> {
  return apiPatch<BusinessProfile>("/business-profile/trading-details", input);
}

export async function updateOperatingHistory(input: Partial<OperatingHistoryInfo>): Promise<BusinessProfile> {
  return apiPatch<BusinessProfile>("/business-profile/operating-history", input);
}

export async function updateSupplierInfo(input: Partial<SupplierInfo>): Promise<BusinessProfile> {
  return apiPatch<BusinessProfile>("/business-profile/suppliers", input);
}
