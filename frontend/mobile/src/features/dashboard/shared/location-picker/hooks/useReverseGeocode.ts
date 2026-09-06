import { useEffect, useRef, useState } from "react";

import { reverseGeocode } from "../services/geocodingService";
import type { GeocodedAddress } from "../types";

/** Waits this long after the pin stops moving before calling the
 *  backend -- matches the Geocoding API's own documented advice on
 *  autocomplete-style calls (debounce rather than firing one request
 *  per tiny map movement). */
const DEBOUNCE_MS = 600;

export function useReverseGeocode(latitude: number | null, longitude: number | null) {
  const [address, setAddress] = useState<GeocodedAddress | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  // Guards against a slow EARLIER lookup overwriting a faster LATER
  // one -- the business may pan again before the previous request
  // returns; only the response matching the most recent request is
  // ever allowed to update state.
  const requestIdRef = useRef(0);

  useEffect(() => {
    if (latitude === null || longitude === null) return;

    const thisRequestId = ++requestIdRef.current;
    setIsLoading(true);
    setFailed(false);

    const timer = setTimeout(() => {
      reverseGeocode(latitude, longitude)
        .then((result) => {
          if (requestIdRef.current === thisRequestId) {
            setAddress(result);
            setIsLoading(false);
          }
        })
        .catch(() => {
          // Never fatal -- the pin's own coordinates are already
          // captured regardless; the business can always fill the
          // text fields in by hand if the lookup itself fails.
          if (requestIdRef.current === thisRequestId) {
            setFailed(true);
            setIsLoading(false);
          }
        });
    }, DEBOUNCE_MS);

    return () => clearTimeout(timer);
  }, [latitude, longitude]);

  return { address, isLoading, failed };
}
