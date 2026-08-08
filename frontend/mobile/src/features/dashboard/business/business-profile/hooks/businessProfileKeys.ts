/** Business Profile — React Query cache keys, user-scoped from the
 *  first draft. Same security reasoning as every other feature: a key
 *  under a shared root risks one business's data flashing on another's
 *  screen right after an account switch on the same device. */

type UserScope = string | undefined;

export const businessProfileKeys = {
  profile: (userId: UserScope) => ["businessProfile", userId ?? "anonymous"] as const,
};
