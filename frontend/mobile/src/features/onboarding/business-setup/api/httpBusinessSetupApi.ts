/**
 * Business setup — real backend implementation.
 *
 * ONE ENDPOINT, AND IT IS READ-ONLY. The steps WRITE through the
 * existing /business-profile PATCH routes (see
 * useBusinessProfileMutations), so a step answered during setup is the
 * same edit as the same field in My Business later: one service, one
 * validation, one write path. A setup flow with its own writer is a
 * second way for the same column to be set, and the two disagree
 * within a month.
 *
 * The backend shape is already this shape — see
 * demand/services/setup_service.py — so there is nothing to map.
 */

import { apiGet } from "@/services/api/apiClient";
import type { SetupState } from "../types";

export async function getSetupState(): Promise<SetupState> {
  return apiGet<SetupState>("/business/setup-state");
}
