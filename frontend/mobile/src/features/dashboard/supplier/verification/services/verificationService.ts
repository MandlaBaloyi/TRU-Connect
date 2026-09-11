/**
 * GET /api/v1/verification/me -- am I visible to buyers?
 *
 * REAL, not mocked, even though USE_MOCK is honoured below like every
 * other service here. The mock returns the HIDDEN state rather than
 * the verified one, which is the opposite of the usual convention of
 * mocking the happy path -- and it is the right way round for this
 * one. A banner that never appears in mock mode is a banner nobody
 * notices is broken.
 */
import { apiGet } from "@/services/api/apiClient";

import type { VerificationStatus } from "../types";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const MOCK_HIDDEN: VerificationStatus = {
  status: "unverified",
  visibleToBuyers: false,
  headline: "Your shop is ready — buyers cannot see it yet.",
  detail:
    "Keep building: your catalogue, prices and settings are all saved. The day your business is verified, everything you have set up becomes visible at once.",
};

export async function getMyVerificationStatus(): Promise<VerificationStatus> {
  if (USE_MOCK) {
    await new Promise<void>((resolve) => setTimeout(resolve, 300));
    return MOCK_HIDDEN;
  }
  return apiGet<VerificationStatus>("/verification/me");
}
