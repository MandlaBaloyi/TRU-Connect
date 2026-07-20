/**
 * Cross-feature shared types. Feature-specific types live under
 * src/features/<feature>/types.ts and should be imported from there
 * directly; only put a type here if more than one feature needs it.
 */
export type { UserRole } from "@/features/auth/types";

export interface ApiListResponse<T> {
  items: T[];
  page: number;
  pageSize: number;
  total: number;
}
