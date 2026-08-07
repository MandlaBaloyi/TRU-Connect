/**
 * The CURRENT user's id, read fresh from the stored access token on
 * every mount. Identical reasoning to loan-book's useCurrentUserId.ts —
 * kept as this feature's own copy rather than a cross-feature import
 * (see types.ts file docstring), but the constraints are the same:
 *
 * - re-reads secureStorage on every mount rather than caching, so a
 *   stale account id can never leak into a query key after logout
 * - uses atob(), NOT Buffer — Buffer is a Node.js global not guaranteed
 *   in Hermes without a polyfill this project doesn't include
 * - never throws on a malformed/missing token
 */

import { useEffect, useState } from "react";

import { secureStorage } from "@/services/storage/secureStorage";
import { STORAGE_KEYS } from "@/constants/config";

function decodeJwtSubject(token: string): string | undefined {
  try {
    const payloadSegment = token.split(".")[1];
    if (!payloadSegment) return undefined;
    const normalized = payloadSegment.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), "=");
    const json = atob(padded);
    const payload = JSON.parse(json) as { sub?: string };
    return payload.sub;
  } catch {
    return undefined;
  }
}

export function useCurrentUserId(): string | undefined {
  const [userId, setUserId] = useState<string | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;
    secureStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN).then((token) => {
      if (cancelled) return;
      setUserId(token ? decodeJwtSubject(token) : undefined);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return userId;
}
