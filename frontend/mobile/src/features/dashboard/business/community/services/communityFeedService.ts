import { MOCK_COMMUNITY_FEED } from "./mockCommunityFeed";
import type { CommunityFeed } from "../types";

/**
 * The Community feed's ONLY data boundary. No hook or screen imports
 * the mock directly, and none calls apiClient itself -- the same rule
 * every other feature in this app follows (see
 * supplierSearchService.ts's own docstring).
 *
 * ALWAYS MOCKED FOR NOW, regardless of EXPO_PUBLIC_USE_MOCK_API, and
 * that is deliberate rather than an oversight. There is no feed
 * endpoint yet. Honouring the flag would mean pointing at a URL that
 * 404s the moment anyone runs the app against the real backend --
 * which is exactly how the whole Community tab would look broken
 * during the rebuild, when every other screen on it is talking to the
 * real API perfectly well.
 *
 * Phase 4 replaces the body of getCommunityFeed with the same
 * `USE_MOCK ? mock : http` switch the other services use. Nothing
 * that imports this file changes.
 */
export async function getCommunityFeed(): Promise<CommunityFeed> {
  // A real delay, not zero: an instantly-resolving promise hides
  // every loading state, and a skeleton nobody has looked at is a
  // skeleton nobody has designed.
  await new Promise((resolve) => setTimeout(resolve, 450));
  return MOCK_COMMUNITY_FEED;
}
