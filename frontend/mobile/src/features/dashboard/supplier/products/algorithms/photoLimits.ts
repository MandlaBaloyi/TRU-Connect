/**
 * Photo limit per subscription tier -- Free 2 / Pro 3 / Max 5. Lives in
 * algorithms/, not services/productMapper.ts, since this is a business
 * RULE with real branches (per-tier ceilings), not a display-formatting
 * transform -- same distinction Loan Book draws between its own
 * algorithms/paymentAllocation.ts and services/loanMapper.ts.
 *
 * MAX = 5 IS NOT A COINCIDENCE -- bulk-products' own import template
 * supports exactly 5 image columns (image_1..image_5), matching Max
 * tier's own ceiling: the template's column count IS the platform-wide
 * upper bound, not a number picked independently. A Free/Pro account
 * whose import row has more filled image columns than their own tier
 * allows gets a clear per-row validation error at import time (see
 * bulk-products' own row validator) -- never a silent drop of the
 * extra photos.
 *
 * ONE SHARED CONSTANT MAP, NOT a different database/table per plan --
 * per review: "don't create different database structures for the
 * plans, the database simply supports multiple media records." This
 * file is that same idea applied client-side: one images array on
 * every Product regardless of tier, one limit function that reads a
 * tier and returns a ceiling.
 *
 * CURRENT REALITY: subscription tier is frontend-only and hardcoded to
 * FREE for every supplier account -- there is no real backend
 * Subscription model yet (confirmed against supplier/my-account's own
 * subscription screens, which are themselves mock-backed). This file
 * accepts a `tier` parameter rather than hardcoding FREE internally,
 * so the moment a real tier concept exists elsewhere in the app, this
 * function doesn't need to change -- only its caller does. Until then,
 * every caller in this feature passes "FREE" explicitly (see
 * ProductPhotosField's own default), which is honest about today's
 * actual behaviour rather than pretending tier-awareness exists when
 * it doesn't yet.
 */

export type SubscriptionTier = "FREE" | "PRO" | "MAX";

const PHOTO_LIMIT_BY_TIER: Record<SubscriptionTier, number> = {
  FREE: 2,
  PRO: 3,
  MAX: 5,
};

export function getPhotoLimit(tier: SubscriptionTier): number {
  return PHOTO_LIMIT_BY_TIER[tier];
}
