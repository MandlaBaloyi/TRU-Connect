import { useEffect, useRef, useState } from "react";

import { generateSessionToken } from "../generateSessionToken";
import { suggestAddress } from "../services/geocodingService";
import type { AddressSuggestion } from "../types";

/** Same debounce window as useReverseGeocode -- Mapbox's own
 *  autocomplete guidance is to debounce keystrokes, not fire one
 *  /suggest call per character. */
const DEBOUNCE_MS = 300;

export function useAddressSearch(proximity?: { latitude: number; longitude: number }) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<AddressSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  // One token per SEARCH SESSION, not per call -- created the moment
  // typing starts from empty, reused for every suggest call in this
  // search, and handed to retrieveAddress by the caller once a
  // suggestion is tapped. A NEW token only gets minted the next time
  // typing starts from empty again (see the effect below) -- exactly
  // matches Mapbox's own "a session begins when the user starts
  // typing and ends when they select a result" definition.
  const sessionTokenRef = useRef(generateSessionToken());
  const requestIdRef = useRef(0);

  useEffect(() => {
    if (!query.trim()) {
      setSuggestions([]);
      return;
    }

    const thisRequestId = ++requestIdRef.current;
    setIsLoading(true);

    const timer = setTimeout(() => {
      suggestAddress(query, sessionTokenRef.current, proximity)
        .then((results) => {
          if (requestIdRef.current === thisRequestId) {
            setSuggestions(results);
            setIsLoading(false);
          }
        })
        .catch(() => {
          // Never fatal -- the pin-drop map is always still there as
          // the primary way to set a location; search is a
          // convenience layered on top of it, not a dependency.
          if (requestIdRef.current === thisRequestId) {
            setSuggestions([]);
            setIsLoading(false);
          }
        });
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, DEBOUNCE_MS);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  const sessionToken = sessionTokenRef.current;

  /** Call once a suggestion has been retrieved and the search is
   *  done -- clears the visible list and mints a fresh session token
   *  for whatever the business searches for next. */
  const completeSession = () => {
    setQuery("");
    setSuggestions([]);
    sessionTokenRef.current = generateSessionToken();
  };

  return { query, setQuery, suggestions, isLoading, sessionToken, completeSession };
}
