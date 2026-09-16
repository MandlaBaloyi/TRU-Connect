/**
 * Business Profile ("My Business" in the UI — see this file's own
 * naming: the PRODUCT name is "My Business", the DOMAIN/feature name
 * is "business-profile", per the spec's explicit instruction not to
 * create a parallel "my-business" feature folder).
 *
 * DATA OWNERSHIP: this is BUSINESS data, separate from personal
 * ACCOUNT data (name, login email, security). Where a business field
 * can reuse a verified account value (phone, email), it stores its own
 * copy with a flag for "same as my account" rather than silently
 * reading the account record every time — see ContactDetails below.
 * This keeps Business Profile independently editable without ever
 * touching account/auth data, and keeps the reverse true too: editing
 * account settings never silently changes business contact info.
 *
 * NOTHING HERE REACHES INTO LOAN BOOK, ORDER BOOK, OR SUPPLIERS.
 * Business Profile is the identity layer those features will
 * eventually reference (business name, category, location) — it does
 * not duplicate or own any of their operational data (customers,
 * orders, entries). Two features modelling similar concepts
 * independently is fine; this feature owning a live copy of another
 * feature's data is not.
 *
 * ONE FIELD CONSOLIDATION WORTH NAMING: the written spec separately
 * asks for "Business operating model" (section 1) and "Operating
 * location" (section 3) — both literally "where do you mainly operate
 * from", same option list. Modelled ONCE here as
 * BusinessDetails.operatingModel, shown in the Location section (where
 * it reads more naturally), rather than as two fields asking the same
 * question — matches the spec's own "do not duplicate information"
 * principle better than implementing the literal redundancy would.
 */

// ---------------------------------------------------------------------------
// Structured option sets — chips/dropdowns/radios, never free text where a
// real option list exists. Every *_LABELS map is what's shown; the union
// type is what's stored, so adding an option later is additive everywhere.
// ---------------------------------------------------------------------------

export type BusinessCategory =
  | "FOOD_BEVERAGES"
  | "CLOTHING_FASHION"
  | "BEAUTY_COSMETICS"
  | "ELECTRONICS"
  | "RETAIL"
  | "PROFESSIONAL_SERVICES"
  | "HOME_HOUSEHOLD"
  | "OTHER";

export const BUSINESS_CATEGORY_LABELS: Record<BusinessCategory, string> = {
  FOOD_BEVERAGES: "Food & Beverages",
  CLOTHING_FASHION: "Clothing & Fashion",
  BEAUTY_COSMETICS: "Beauty & Cosmetics",
  ELECTRONICS: "Electronics",
  RETAIL: "Retail",
  PROFESSIONAL_SERVICES: "Professional Services",
  HOME_HOUSEHOLD: "Home & Household",
  OTHER: "Other",
};

/** Category -> starter product/service chip options for Trading Details
 *  §1. Deliberately small, illustrative lists, not a catalogue — see
 *  this file's own docstring on why Business Profile never becomes the
 *  marketplace catalogue. OTHER always included so nothing is a dead
 *  end. */
export const PRODUCT_OPTIONS_BY_CATEGORY: Partial<Record<BusinessCategory, string[]>> = {
  BEAUTY_COSMETICS: ["Perfumes", "Body lotions", "Hair products", "Makeup", "Skincare", "Other"],
  FOOD_BEVERAGES: ["Cooked food", "Snacks", "Drinks", "Groceries", "Other"],
  CLOTHING_FASHION: ["Clothing", "Shoes", "Accessories", "Bags", "Other"],
};
export const DEFAULT_PRODUCT_OPTIONS = ["Products", "Services", "Other"];

export type BusinessType =
  | "SOLE_TRADER"
  | "PARTNERSHIP"
  | "FAMILY_BUSINESS"
  | "REGISTERED_COMPANY"
  | "OTHER";

export const BUSINESS_TYPE_LABELS: Record<BusinessType, string> = {
  SOLE_TRADER: "Sole trader",
  PARTNERSHIP: "Partnership",
  FAMILY_BUSINESS: "Family business",
  REGISTERED_COMPANY: "Registered company",
  OTHER: "Other",
};

/** Shared by BusinessDetails.operatingModel — see file docstring on the
 *  section-1/section-3 consolidation. */
export type OperatingModel =
  | "HOME"
  | "SHOP"
  | "MARKET_STALL"
  | "STREET_MOBILE"
  | "ONLINE"
  | "MULTIPLE_LOCATIONS"
  | "OTHER";

export const OPERATING_MODEL_LABELS: Record<OperatingModel, string> = {
  HOME: "Home",
  SHOP: "Shop",
  MARKET_STALL: "Market / stall",
  STREET_MOBILE: "Street / mobile",
  ONLINE: "Online",
  MULTIPLE_LOCATIONS: "Multiple locations",
  OTHER: "Other",
};

export type CustomerType = "INDIVIDUALS" | "OTHER_BUSINESSES" | "FRIENDS_COMMUNITY" | "ORGANISATIONS" | "OTHER";

export type RestockRhythm =
  | "DAILY" | "TWICE_WEEKLY" | "WEEKLY" | "FORTNIGHTLY" | "MONTHLY" | "IRREGULAR";

export const RESTOCK_RHYTHM_LABELS: Record<RestockRhythm, string> = {
  DAILY: "Every day",
  TWICE_WEEKLY: "Twice a week",
  WEEKLY: "Once a week",
  FORTNIGHTLY: "Every two weeks",
  MONTHLY: "Once a month",
  IRREGULAR: "When I run out",
};

export type WeeklySpendBand =
  | "UNDER_500" | "R500_TO_2000" | "R2000_TO_5000" | "R5000_TO_10000" | "OVER_10000";

/** A BAND, NEVER A NUMBER. An exact figure is a question people
 *  hesitate over and feel examined by, and the engine only needs enough
 *  to stop showing a R5,000 pallet to a shop that buys R800 a week. */
export const WEEKLY_SPEND_BAND_LABELS: Record<WeeklySpendBand, string> = {
  UNDER_500: "Under R500",
  R500_TO_2000: "R500 – R2 000",
  R2000_TO_5000: "R2 000 – R5 000",
  R5000_TO_10000: "R5 000 – R10 000",
  OVER_10000: "More than R10 000",
};

export const CUSTOMER_TYPE_LABELS: Record<CustomerType, string> = {
  INDIVIDUALS: "Individuals",
  OTHER_BUSINESSES: "Other businesses",
  FRIENDS_COMMUNITY: "Friends / community",
  ORGANISATIONS: "Organisations",
  OTHER: "Other",
};



export type Weekday = "MON" | "TUE" | "WED" | "THU" | "FRI" | "SAT" | "SUN";

export const WEEKDAY_LABELS: Record<Weekday, string> = {
  MON: "Monday",
  TUE: "Tuesday",
  WED: "Wednesday",
  THU: "Thursday",
  FRI: "Friday",
  SAT: "Saturday",
  SUN: "Sunday",
};

export const WEEKDAYS_ORDER: Weekday[] = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"];
export const WEEKDAY_PRESETS: Record<"WEEKDAYS" | "WEEKENDS" | "EVERY_DAY", Weekday[]> = {
  WEEKDAYS: ["MON", "TUE", "WED", "THU", "FRI"],
  WEEKENDS: ["SAT", "SUN"],
  EVERY_DAY: ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
};

export type EmployeeRange = "JUST_ME" | "TWO_TO_FIVE" | "SIX_TO_TEN" | "ELEVEN_TO_TWENTY" | "MORE_THAN_TWENTY";

export const EMPLOYEE_RANGE_LABELS: Record<EmployeeRange, string> = {
  JUST_ME: "Just me",
  TWO_TO_FIVE: "2–5",
  SIX_TO_TEN: "6–10",
  ELEVEN_TO_TWENTY: "11–20",
  MORE_THAN_TWENTY: "More than 20",
};

export type OperatingHistory =
  | "LESS_THAN_6_MONTHS"
  | "SIX_MONTHS_TO_1_YEAR"
  | "ONE_TO_2_YEARS"
  | "TWO_TO_5_YEARS"
  | "FIVE_PLUS_YEARS";

export const OPERATING_HISTORY_LABELS: Record<OperatingHistory, string> = {
  LESS_THAN_6_MONTHS: "Less than 6 months",
  SIX_MONTHS_TO_1_YEAR: "6 months – 1 year",
  ONE_TO_2_YEARS: "1–2 years",
  TWO_TO_5_YEARS: "2–5 years",
  FIVE_PLUS_YEARS: "5+ years",
};

export type SupplierSource =
  | "LOCAL_SUPPLIERS"
  | "WHOLESALERS"
  | "DISTRIBUTORS"
  | "MANUFACTURERS"
  | "MARKETS"
  | "OTHER_BUSINESSES"
  | "OTHER";

export const SUPPLIER_SOURCE_LABELS: Record<SupplierSource, string> = {
  LOCAL_SUPPLIERS: "Local suppliers",
  WHOLESALERS: "Wholesalers",
  DISTRIBUTORS: "Distributors",
  MANUFACTURERS: "Manufacturers",
  MARKETS: "Markets",
  OTHER_BUSINESSES: "Other businesses",
  OTHER: "Other",
};

/** The 9 South African provinces — a real, closed, small list, so a
 *  dropdown rather than free text is genuinely appropriate here (unlike
 *  city/town, which has far too many values to enumerate). */
export type SouthAfricanProvince =
  | "EASTERN_CAPE" | "FREE_STATE" | "GAUTENG" | "KWAZULU_NATAL" | "LIMPOPO"
  | "MPUMALANGA" | "NORTHERN_CAPE" | "NORTH_WEST" | "WESTERN_CAPE";

export const PROVINCE_LABELS: Record<SouthAfricanProvince, string> = {
  EASTERN_CAPE: "Eastern Cape",
  FREE_STATE: "Free State",
  GAUTENG: "Gauteng",
  KWAZULU_NATAL: "KwaZulu-Natal",
  LIMPOPO: "Limpopo",
  MPUMALANGA: "Mpumalanga",
  NORTHERN_CAPE: "Northern Cape",
  NORTH_WEST: "North West",
  WESTERN_CAPE: "Western Cape",
};

// ---------------------------------------------------------------------------
// The seven sections
// ---------------------------------------------------------------------------

/** Section 1 — required, the fastest to complete. */
export interface BusinessDetails {
  businessName: string;
  category?: BusinessCategory;
  businessType?: BusinessType;
  description?: string;
  /** Where the business mainly operates from — see file docstring for
   *  why this lives here and isn't duplicated as a Location-section
   *  field too. */
  operatingModel?: OperatingModel;
}

/** Section 2 — every field can lean on the verified account value
 *  instead of asking again. `usesSameAsAccountPhone`/`Email` are what
 *  actually drive that — the phone/email strings themselves are always
 *  populated (copied at edit time) so nothing downstream needs to know
 *  about account data just to render a business contact card. */
export interface ContactDetails {
  phone?: string;
  usesSameAsAccountPhone: boolean;
  email?: string;
  usesSameAsAccountEmail: boolean;
  whatsapp?: string;
  whatsappSameAsPhone: boolean;
  whatsappNotUsed: boolean;
  facebook?: string;
  instagram?: string;
}

/** Section 3 — informal-business-appropriate: town/area, not a formal
 *  postal address. */
export interface BusinessLocation {
  province?: SouthAfricanProvince;
  cityOrTown?: string;
  /** Optional, only if the shop owner wants to give more than
   *  town/area. Never required — see spec's "do not require a street
   *  address" rule. */
  physicalAddress?: string;
  /** Set only if the user granted permission — see
   *  hooks/useCurrentLocation.ts. Absence is a normal, fully
   *  supported state, never blocking. */
  latitude?: number;
  longitude?: number;
}

/** Section 4 — the richest section; this is what makes the profile
 *  genuinely useful to Order Book/Loan Book/future features, not just
 *  a business card. */
export interface TradingDetails {
  /** WHAT THEY BUY, as ProductCategory values — the same taxonomy the
   *  catalogue and the category chips use. Replaces `products`, which
   *  asked what they SELL from a per-category list that offered five of
   *  eight business categories the answer "Products".
   *
   *  A salon SELLS haircuts and BUYS relaxers; only the second is
   *  orderable here, and only the second tells the feed anything. */
  buysCategories: string[];
  customerTypes: CustomerType[];
  /** The two questions that make the feed useful before a first order.
   *  Undefined until asked — never defaulted to a guess, because a
   *  wrong declared cadence is indistinguishable from a real one. */
  restockRhythm?: RestockRhythm;
  weeklySpendBand?: WeeklySpendBand;
  /** Can this shop fetch its own stock?
   *
   *  THREE STATES, and `null` is a real one — "never asked". It must
   *  not collapse into false anywhere: the "Collect near you" rail is
   *  withheld only from a shop that has actually SAID it cannot
   *  collect, never from one that simply predates the question.
   *  `undefined` here means the same thing as null on the wire. */
  canCollect?: boolean | null;
  operatingDays: Weekday[];
  openingTime?: string; // "HH:mm", optional
  closingTime?: string; // "HH:mm", optional
  employeeRange?: EmployeeRange;
}

/** Section 5 — lightweight, no financial detail requested. */
export interface OperatingHistoryInfo {
  yearsOperating?: OperatingHistory;
}

/** Section 6 — deliberately shallow: which KIND of source, never a
 *  named supplier record. Real supplier relationships live in the
 *  Supplier Network, not here. */
export interface SupplierInfo {
  sources: SupplierSource[];
}

/** SECTION 7 WAS "VerificationStatus" AND IS GONE (V2_18 Part 2).
 *
 *  identityVerified and documentsVerified went first: they were the
 *  SUPPLIER model's concepts on a business, with no backing system,
 *  false on every row that ever existed. The verification curtain
 *  gates who may SELL; an informal business is not checked in order to
 *  shop.
 *
 *  The four that remained went for the same reason once anyone looked
 *  at what they could actually say. phoneVerified could only ever be
 *  true (the endpoint is @fully_authenticated, so the OTP is done by
 *  definition). emailVerified could only ever be false (there is no
 *  email-verification flow). businessInfoComplete and locationComplete
 *  were never written by anything.
 *
 *  Completeness itself is still measured, and better: see
 *  algorithms/completionCalculator.ts, which derives it from the data
 *  rather than from a column somebody has to remember to set. */

/** The whole profile, one business per user for now (modelled so a
 *  second business later is an additive change, not a rewrite). */
export interface BusinessProfile {
  id: string;
  businessDetails: BusinessDetails;
  contactDetails: ContactDetails;
  location: BusinessLocation;
  tradingDetails: TradingDetails;
  operatingHistory: OperatingHistoryInfo;
  supplierInfo: SupplierInfo;
  createdAt: string;
  updatedAt: string;
}

/** Per-section completion, feeding both the overall progress bar and
 *  each accordion header's own state — see
 *  services/completionCalculator.ts, the only place this is computed. */
export type ProfileSectionKey =
  | "businessDetails"
  | "contactDetails"
  | "location"
  | "tradingDetails"
  | "operatingHistory"
  | "supplierInfo";

export interface ProfileCompletion {
  overallPercent: number;
  sections: Record<
    ProfileSectionKey,
    { isComplete: boolean; requiredFieldsMet: number; requiredFieldsTotal: number }
  >;
}
