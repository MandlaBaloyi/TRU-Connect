/**
 * The CURRENT user's id, read fresh from the stored access token on
 * every mount. Kept as THIS FEATURE'S OWN copy -- same convention
 * every other feature in this app follows (products, bulk-products,
 * order-book, loan-book all carry their own identical copy).
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
