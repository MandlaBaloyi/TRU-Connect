/**
 * Supplier My Account service — mock-backed for everything that isn't
 * real yet, but genuinely real for the supplier's own profile (see
 * that section below) -- the first piece of this whole file to
 * graduate from mock, replaced in place rather than rewritten, same
 * "replace the function body, not the signature" plan this file's own
 * business-name section already anticipated before this update.
 *
 * Smaller surface than the business version on purpose — see
 * types.ts's header for why payment methods aren't here at all, not
 * even as stubs.
 */
import { apiGet, apiPatch } from "@/services/api/apiClient";
import type {
  ConnectCode,
  DeactivationRequestStatus,
  DeleteAccountInput,
  DeletionRequestStatus,
  DisplayNameInput,
} from "../types";

const latency = () => new Promise<void>((resolve) => setTimeout(resolve, 300));
const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

// --- Contact details --------------------------------------------------
// PHONE/EMAIL THEMSELVES ARE REAL — from AuthUser via useCurrentUser
// (GET /auth/me). No PATCH exists yet, so this simulates one — same
// session-persistent mock discipline as business/my-account's own
// updateContactField: the caller writes the result into the SAME
// React Query cache key useCurrentUser reads (see
// hooks/useContactDetails.ts), so the UI never shows a value that
// reverts on the next real-looking fetch.

export type ContactField = "phone" | "email";

export async function updateContactField(field: ContactField, value: string): Promise<string> {
  await latency();
  const trimmed = value.trim();
  if (field === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
    throw new Error("Enter a valid email address.");
  }
  if (field === "phone" && trimmed.replace(/\D/g, "").length < 9) {
    throw new Error("Enter a valid phone number.");
  }
  return trimmed;
}

export async function updateDisplayName(input: DisplayNameInput): Promise<DisplayNameInput> {
  await latency();
  const firstName = input.firstName.trim();
  const lastName = input.lastName.trim();
  if (firstName.length === 0) {
    throw new Error("Enter your first name.");
  }
  return { firstName, lastName };
}

// --- Supplier profile (business name, bio/description, contact channels) --
// GENUINELY REAL NOW -- GET/PATCH /supplier-discovery/my-profile, the
// first real write path this whole domain has ever had. Everything
// below used to be two separate in-memory mocks (business name, bio)
// with no real endpoint behind either; both are now the SAME single
// real profile, matching the real backend's own shape exactly (one
// SupplierProfile row, one PATCH updates all of it together, not
// piecemeal). "bio" here is genuinely SupplierProfile.description --
// see this section's own history for why that was already true even
// before this became real.

export interface SupplierProfileData {
  businessName: string;
  category: string | null;
  location: string | null;
  description: string | null;
  photoVisibility: string;
  visibleImageSource: string;
  /** Currently-approved profile photo / cover banner, or null. Written
   *  by the real image-upload flow (services/profileImageUpload.ts) and
   *  returned by GET /my-profile -- the displayed image is always
   *  whatever the profile says, never local device state. */
  businessImageUrl: string | null;
  coverImageUrl: string | null;
  whatsappNumber: string | null;
  contactEmail: string | null;
  tiktokHandle: string | null;
  shareContactDetails: boolean;
  /** Fulfilment terms shown UNGATED on the business-facing profile --
   *  "do you deliver" and "what's your minimum order" are what a
   *  business needs while deciding whether to connect at all.
   *  minimumOrderCents null means no minimum (never 0). */
  /** TRI-STATE: null until the supplier actually chooses. */
  offersDelivery: boolean | null;
  minimumOrderCents: number | null;
  /** The supplier's own fixed premises -- what a connected business
   *  sees as "Collect from" on the profile, and at checkout when they
   *  choose COLLECT. Structured (not one text blob) because the
   *  business-facing screens format it themselves, and because the
   *  coordinates make a future "open in maps" real rather than a
   *  re-geocode. */
  collectionBuilding: string | null;
  collectionStreet: string | null;
  collectionSuburb: string | null;
  collectionCity: string | null;
  collectionProvince: string | null;
  collectionPostalCode: string | null;
  collectionLatitude: number | null;
  collectionLongitude: number | null;
  /** "Show businesses when I was last online." Opt-in — false is a
   *  real, complete answer that asserts nothing about the supplier. */
  showLastActive: boolean;
  /** "Show businesses my track record." Defaults TRUE — every public
   *  figure is a count that hides at zero, so there's no arrangement
   *  of the data that can make a supplier look bad by default. */
  showTrackRecord: boolean;
  /** READ-ONLY. The supplier's own last-active time, so the setting can
   *  show them exactly what a business would see. Never sent back on a
   *  save; the server owns it (see core/decorators._touch_last_active). */
  lastActiveAt?: string | null;
  /** READ-ONLY. The supplier's OWN performance figures — a different
   *  set from what businesses see, because the two audiences need
   *  opposite things: businesses need signals that are fair to a
   *  newcomer, a supplier needs signals that say what to fix. Always
   *  returned; showTrackRecord only controls the BUSINESS-facing
   *  view. */
  performance?: SupplierPerformance | null;
}

export interface SupplierPerformance {
  /** Recent decided orders (accepted or declined), and how many of
   *  those were accepted. A recent window, so improvement actually
   *  shows — an all-time rate can never recover. */
  decidedCount: number;
  acceptedCount: number;
  /** Median hours from submitted to decided. Null if nothing decided. */
  medianResponseHours: number | null;
  totalSalesCents: number;
  unitsSoldCount: number;
  ordersThisMonth: number;
  /** Orders this supplier accepted and then cancelled themselves.
   *  Business-initiated cancellations are excluded — someone else's
   *  change of mind isn't the supplier's record. */
  cancelledAfterConfirming: number;
  /** Businesses that have had MORE THAN ONE order accepted. The
   *  hardest signal in this data to fake — coming back is a verdict on
   *  the first order that no self-reported claim can imitate.
   *
   *  PRIVATE. It used to be a public track-record column; it moved
   *  here because it says how the supplier PERFORMS rather than where
   *  they STAND, and acting on it is their own business. */
  repeatBusinessCount: number;
}

let mockProfile: SupplierProfileData = {
  businessName: "Your Business",
  category: null,
  location: null,
  description: null,
  photoVisibility: "connections",
  visibleImageSource: "none",
  businessImageUrl: null,
  coverImageUrl: null,
  whatsappNumber: null,
  contactEmail: null,
  tiktokHandle: null,
  shareContactDetails: false,
  offersDelivery: null,
  minimumOrderCents: null,
  collectionBuilding: null,
  collectionStreet: null,
  collectionSuburb: null,
  collectionCity: null,
  collectionProvince: null,
  collectionPostalCode: null,
  collectionLatitude: null,
  collectionLongitude: null,
  showLastActive: false,
  lastActiveAt: null,
  showTrackRecord: true,
  performance: null,
};

export async function getMyProfile(): Promise<SupplierProfileData> {
  if (USE_MOCK) {
    await latency();
    return mockProfile;
  }
  return apiGet<SupplierProfileData>("/supplier-discovery/my-profile");
}

export async function updateMyProfile(input: SupplierProfileData): Promise<SupplierProfileData> {
  if (USE_MOCK) {
    await latency();
    const businessName = input.businessName.trim();
    if (businessName.length === 0) {
      throw new Error("Enter your business name.");
    }
    mockProfile = { ...input, businessName };
    return mockProfile;
  }
  return apiPatch<SupplierProfileData>("/supplier-discovery/my-profile", {
    business_name: input.businessName,
    category: input.category,
    location: input.location,
    description: input.description,
    photo_visibility: input.photoVisibility,
    visible_image_source: input.visibleImageSource,
    whatsapp_number: input.whatsappNumber,
    contact_email: input.contactEmail,
    tiktok_handle: input.tiktokHandle,
    share_contact_details: input.shareContactDetails,
    offers_delivery: input.offersDelivery,
    minimum_order_cents: input.minimumOrderCents,
    collection_building: input.collectionBuilding,
    collection_street: input.collectionStreet,
    collection_suburb: input.collectionSuburb,
    collection_city: input.collectionCity,
    collection_province: input.collectionProvince,
    collection_postal_code: input.collectionPostalCode,
    collection_latitude: input.collectionLatitude,
    collection_longitude: input.collectionLongitude,
    show_last_active: input.showLastActive,
    show_track_record: input.showTrackRecord,
  });
}

// --- Account lifecycle requests ------------------------------------------
// Same non-negotiable rule as business/my-account/services/accountService.ts:
// these functions NEVER touch real accountStatus. accountStatus is
// read-only, straight from useCurrentUser(). This only simulates
// SUBMITTING a request.

let deactivationRequestState: DeactivationRequestStatus = "NONE";
let deletionRequestState: DeletionRequestStatus = "NONE";

export async function getDeactivationRequestStatus(): Promise<DeactivationRequestStatus> {
  await latency();
  return deactivationRequestState;
}

export async function requestDeactivation(): Promise<DeactivationRequestStatus> {
  await latency();
  deactivationRequestState = "SUBMITTED";
  return deactivationRequestState;
}

export async function getDeletionRequestStatus(): Promise<DeletionRequestStatus> {
  await latency();
  return deletionRequestState;
}

export async function requestAccountDeletion(input: DeleteAccountInput): Promise<DeletionRequestStatus> {
  await latency();
  // NEVER log `input` — it carries a plaintext password.
  if (!input.currentPassword) {
    throw new Error("Enter your password to confirm.");
  }
  deletionRequestState = "SUBMITTED";
  return deletionRequestState;
}

// --- Connect Code (QR) ----------------------------------------------------
// Mirrors business/my-account/services/accountService.ts's own Connect
// Code section exactly — same reasoning, same mock discipline. See
// this feature's types.ts for the one real difference (direction of
// scanning).

function generateMockToken(): string {
  const bytes = Array.from({ length: 16 }, () => Math.floor(Math.random() * 256));
  return bytes.map((b) => b.toString(16).padStart(2, "0")).join("");
}

let connectCodeState: ConnectCode = { token: generateMockToken(), createdAt: new Date().toISOString() };

export async function getConnectCode(): Promise<ConnectCode> {
  await latency(150);
  return connectCodeState;
}

export async function regenerateConnectCode(): Promise<ConnectCode> {
  await latency(300);
  connectCodeState = { token: generateMockToken(), createdAt: new Date().toISOString() };
  return connectCodeState;
}
