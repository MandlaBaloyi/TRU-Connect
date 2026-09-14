import * as mockApi from "./mockCommunityFeed";
import { getCommunityFeed as httpGetCommunityFeed } from "./httpCommunityFeedService";
import type { CommunityFeed } from "../types";

/**
 * The Community feed's ONLY data boundary. No hook or screen imports
 * the mock directly, and none calls apiClient itself -- the same rule
 * every other feature in this app follows (see
 * supplierSearchService.ts's own docstring).
 *
 * NOW SWITCHED LIKE EVERY OTHER SERVICE. It used to be pinned to the
 * mock REGARDLESS of EXPO_PUBLIC_USE_MOCK_API, because there was no
 * feed endpoint and honouring the flag would have 404'd the whole tab
 * the moment anyone ran against the real backend. The endpoint exists
 * now -- and the server composes the same section shapes the mock did,
 * so nothing that imports this file changes.
 */
const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

export async function getCommunityFeed(): Promise<CommunityFeed> {
  if (!USE_MOCK) return httpGetCommunityFeed();

  // A real delay, not zero: an instantly-resolving promise hides every
  // loading state, and a skeleton nobody has looked at is a skeleton
  // nobody has designed.
  await new Promise((resolve) => setTimeout(resolve, 450));
  return mockApi.MOCK_COMMUNITY_FEED;
}
