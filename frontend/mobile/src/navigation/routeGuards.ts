import { secureStorage } from "@/services/storage/secureStorage";
import { STORAGE_KEYS } from "@/constants/config";
import type { UserRole } from "@/features/auth/types";

/**
 * Route-guard helpers used by Expo Router screens/layouts to decide
 * whether a user may access a given route. Kept framework-agnostic (no
 * direct dependency on expo-router) so it can be unit tested in isolation.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Overall User Flow),
 * docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt.
 */
export async function isAuthenticated(): Promise<boolean> {
  const token = await secureStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  return !!token;
}

export async function getSelectedRole(): Promise<UserRole | null> {
  const role = await secureStorage.getItem(STORAGE_KEYS.SELECTED_ROLE);
  return role === "business" || role === "supplier" ? role : null;
}
