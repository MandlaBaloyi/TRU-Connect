/**
 * Business setup — mock implementation.
 *
 * ANSWERS "NOTHING DONE YET", because that is the state the flow
 * exists for and the only one worth seeing without a backend. Mock
 * mode has no profile to read, so a mock that claimed setup was
 * complete would make the three screens unreachable in exactly the
 * mode somebody would use to look at them.
 */

import type { SetupState } from "../types";

export async function getSetupState(): Promise<SetupState> {
  return {
    steps: { whatYouBuy: false, howYouBuy: false, whereYouAre: false },
    requiredComplete: false,
    isComplete: false,
    nextStep: "whatYouBuy",
  };
}
