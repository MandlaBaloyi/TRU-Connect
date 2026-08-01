import { secureStorage } from "@/services/storage/secureStorage";
import { STORAGE_KEYS } from "@/constants/config";
import type { UserRole } from "@/features/auth/types";

/**
 * Route-guard helpers. Framework-agnostic (no expo-router import) so they
 * can be unit tested in isolation.
 * Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt
 */

export async function isAuthenticated(): Promise<boolean> {
  const token = await secureStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  return !!token;
}

function parseRole(value: string | null): UserRole | null {
  return value === "business" || value === "supplier" || value === "admin" ? value : null;
}

/** Role chosen during onboarding, before any account exists. */
export async function getSelectedRole(): Promise<UserRole | null> {
  return parseRole(await secureStorage.getItem(STORAGE_KEYS.SELECTED_ROLE));
}

/** Authoritative role returned by the backend on register/login. */
export async function getUserRole(): Promise<UserRole | null> {
  return parseRole(await secureStorage.getItem(STORAGE_KEYS.USER_ROLE));
}

/**
 * Role that should decide routing.
 *
 * Prefers the backend-issued role and falls back to the onboarding
 * choice. The order matters: a returning user who signs in on a fresh
 * install never touches the onboarding role picker, so SELECTED_ROLE
 * would be empty and every supplier would land on the business dashboard.
 */
export async function getEffectiveRole(): Promise<UserRole | null> {
  return (await getUserRole()) ?? (await getSelectedRole());
}