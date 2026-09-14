import { apiGet } from "@/services/api/apiClient";
import type { CommunityFeed } from "../types";

/**
 * The real feed. GET /community/feed returns { sections: [...] }, which
 * IS the CommunityFeed shape, so there is no mapping layer here on
 * purpose -- the server composes sections in the shape the app's own
 * components already render.
 *
 * ONE ENDPOINT, BOTH ROLES. The server reads the role off the token and
 * composes a market for a business or a demand signal for a supplier
 * (see feed_service). The app never asks for a role, because a role a
 * caller can ask for is a role a caller can lie about.
 *
 * UNKNOWN SECTION TYPES ARE SKIPPED BY THE RENDERER, not rejected here.
 * That is the property that lets a new rail ship server-side without an
 * app release, and validating strictly would throw it away.
 */
export async function getCommunityFeed(): Promise<CommunityFeed> {
  const data = await apiGet<CommunityFeed>("/community/feed");
  return { sections: data?.sections ?? [] };
}
