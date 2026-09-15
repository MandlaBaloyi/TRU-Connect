import { getBusinessProfile } from "@/features/dashboard/business/business-profile/api/mockBusinessProfileApi";

import type { SetupState, SetupStepId } from "../types";

/**
 * Business setup — mock implementation.
 *
 * IT READS THE MOCK PROFILE RATHER THAN ANSWERING A CONSTANT, and that
 * is not polish -- a hardcoded "nothing done yet" was a trap. The steps
 * write through mockBusinessProfileApi, which really does persist for
 * the session, but a constant here would keep reporting the steps
 * unanswered: finish step one, get sent back to step one, forever, with
 * no way to reach the dashboard in mock mode at all.
 *
 * SO IT MIRRORS backend setup_service._completed, FIELD FOR FIELD.
 * Two copies of a rule is normally the thing to avoid, and the
 * alternative here is worse: a mock that cannot answer the question
 * makes the whole flow untestable without a backend, which is the one
 * job mock mode has. Keeping the two honest is why both sides name the
 * same three steps in the same file-level type.
 *
 * IMPORTS THE MOCK BY NAME, deliberately breaking the usual "never
 * import the mock or http module directly" rule -- this IS the mock
 * module, and reaching for the businessProfileApi seam instead would
 * make the mock's answer depend on EXPO_PUBLIC_USE_MOCK_API, which is
 * already false whenever this file is not the one being used.
 */
export async function getSetupState(): Promise<SetupState> {
  const profile = await getBusinessProfile();
  const trading = profile.tradingDetails;

  const steps: Record<SetupStepId, boolean> = {
    whatYouBuy: (trading.buysCategories?.length ?? 0) > 0,
    // BOTH HALVES, matching the backend: rhythm sets when the feed
    // presses, spend sets what size of basket it may show.
    howYouBuy: Boolean(trading.restockRhythm) && Boolean(trading.weeklySpendBand),
    whereYouAre: profile.location.latitude != null && profile.location.longitude != null,
  };

  const order: SetupStepId[] = ["whatYouBuy", "howYouBuy", "whereYouAre"];
  const missing = order.filter((step) => !steps[step]);

  return {
    steps,
    requiredComplete: steps.whatYouBuy && steps.howYouBuy,
    isComplete: missing.length === 0,
    nextStep: missing[0] ?? null,
  };
}
