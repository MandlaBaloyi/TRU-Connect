import { useEffect, useState } from "react";

import { secureStorage } from "@/services/storage/secureStorage";
import { STORAGE_KEYS } from "@/constants/config";

/**
 * The CURRENT user's id, read fresh from the stored access token every
 * time this hook mounts -- no separate USER_ID storage key exists yet
 * (see persistSession.ts), and the backend already puts exactly this
 * value in the token's `sub` claim
 * (create_access_token(identity=str(business_id))), so this reads it
 * back rather than introducing a second, redundant place to store the
 * same fact.
 *
 * DELIBERATELY re-reads secureStorage on every mount via useEffect,
 * rather than caching the result in React Query -- caching this value
 * would reintroduce the exact staleness bug loanBookKeys.ts's own
 * per-user scoping exists to eliminate: if account A's id got cached
 * and logout cleanup didn't run for any reason, account B would
 * silently query using A's id. secureStorage reads are local-device and
 * fast, so re-reading fresh each time costs nothing meaningful.
 *
 * Uses atob(), NOT Buffer, to decode the token's base64 payload --
 * Buffer is a Node.js global and is NOT guaranteed to exist in React
 * Native's Hermes runtime without an explicit polyfill this project
 * doesn't include. atob() is a real global in modern Hermes (and in
 * every browser), so it works without any extra dependency. Verified:
 * decodes a real-shaped token correctly, never throws on garbage input.
 *
 * JWTs are SIGNED, not encrypted -- reading the payload here does not
 * require (or perform) signature verification, since this only reads
 * back the device's OWN token, already trusted because secure storage
 * on this device wrote it. The backend is the only place that ever
 * needs to verify the signature.
 */

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
    // Malformed or missing token -- never throws, matches every other
    // "not found" contract already used throughout this feature.
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