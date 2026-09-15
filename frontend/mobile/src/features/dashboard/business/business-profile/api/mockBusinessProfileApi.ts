/**
 * Business Profile — mock data source. Written as though Flask already
 * exists, same discipline as every other feature's mock API in this
 * project: every function's signature/shape is exactly what
 * httpBusinessProfileApi.ts will have once the backend is built.
 *
 * SEEDED AS THOUGH SIGNUP ALREADY RAN. businessName, and the account's
 * verified phone/email, are pre-populated here exactly the way the
 * spec requires them to arrive pre-filled — "do not ask for
 * information already known by the account system." Once a real
 * "current user" endpoint exists, this seed is what that endpoint
 * replaces; nothing about the shape needs to change, only where the
 * values come from.
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

const SIMULATED_LATENCY_MS = 220;

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), SIMULATED_LATENCY_MS));
}

export class BusinessProfileError extends Error {
  code: string;
  constructor(message: string, code: string) {
    super(message);
    this.name = "BusinessProfileError";
    this.code = code;
  }
}

// ---------------------------------------------------------------------------
// Seed — pre-filled from "signup", same test identity used elsewhere in
// this project (Mandla Baloyi) for continuity while testing.
// ---------------------------------------------------------------------------

let profile: BusinessProfile = {
  id: "profile-0001",
  businessDetails: {
    businessName: "Mandla's Perfumes",
    category: "BEAUTY_COSMETICS",
    businessType: "SOLE_TRADER",
    description: "I sell perfumes, fragrances and beauty products.",
    operatingModel: "HOME",
  },
  contactDetails: {
    phone: "0821234567",
    usesSameAsAccountPhone: true,
    email: "owner@example.com",
    usesSameAsAccountEmail: true,
    whatsapp: "0821234567",
    whatsappSameAsPhone: true,
    whatsappNotUsed: false,
  },
  location: {
    province: "GAUTENG",
    cityOrTown: "Johannesburg",
  },
  tradingDetails: {
    buysCategories: ["FOOD_GROCERY", "BEVERAGES", "BAKERY"],
    restockRhythm: "TWICE_WEEKLY",
    weeklySpendBand: "R500_TO_2000",
    customerTypes: ["INDIVIDUALS"],
    operatingDays: ["MON", "TUE", "WED", "THU", "FRI", "SAT"],
  },
  operatingHistory: {},
  supplierInfo: { sources: [] },
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

function touch() {
  profile = { ...profile, updatedAt: new Date().toISOString() };
}

// ---------------------------------------------------------------------------
// Reads
// ---------------------------------------------------------------------------

export async function getBusinessProfile(): Promise<BusinessProfile> {
  return delay(profile);
}

// ---------------------------------------------------------------------------
// Writes — one function per section, matching "each section
// independently editable" (never a single giant save-everything call).
// ---------------------------------------------------------------------------

export async function updateBusinessDetails(input: Partial<BusinessDetails>): Promise<BusinessProfile> {
  if (input.businessName !== undefined && input.businessName.trim().length === 0) {
    throw new BusinessProfileError("Give your business a name.", "INVALID_BUSINESS_NAME");
  }
  profile = { ...profile, businessDetails: { ...profile.businessDetails, ...input } };
  touch();
  return delay(profile);
}

export async function updateContactDetails(input: Partial<ContactDetails>): Promise<BusinessProfile> {
  profile = { ...profile, contactDetails: { ...profile.contactDetails, ...input } };
  touch();
  return delay(profile);
}

export async function updateLocation(input: Partial<BusinessLocation>): Promise<BusinessProfile> {
  profile = { ...profile, location: { ...profile.location, ...input } };
  touch();
  return delay(profile);
}

export async function updateTradingDetails(input: Partial<TradingDetails>): Promise<BusinessProfile> {
  profile = { ...profile, tradingDetails: { ...profile.tradingDetails, ...input } };
  touch();
  return delay(profile);
}

export async function updateOperatingHistory(input: Partial<OperatingHistoryInfo>): Promise<BusinessProfile> {
  profile = { ...profile, operatingHistory: { ...profile.operatingHistory, ...input } };
  touch();
  return delay(profile);
}

export async function updateSupplierInfo(input: Partial<SupplierInfo>): Promise<BusinessProfile> {
  profile = { ...profile, supplierInfo: { ...profile.supplierInfo, ...input } };
  touch();
  return delay(profile);
}
