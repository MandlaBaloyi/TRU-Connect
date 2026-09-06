/**
 * Generates a fresh ID for one Search Box search session -- passed to
 * every /suggest call and the one /retrieve call that completes a
 * search, then thrown away. This is purely a billing-grouping token,
 * not a security value, so a lightweight Math.random()-based
 * generator is genuinely sufficient here -- doesn't warrant adding a
 * real UUID dependency (crypto.randomUUID() isn't reliably available
 * across every Hermes/RN runtime this app targets) for something with
 * no security requirement, just "distinct enough across concurrent
 * sessions" per Mapbox's own stated requirement.
 */
export function generateSessionToken(): string {
  return "sess-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
}
