/**
 * useOrderCustomerSearch — customer lookup for the create-order flow.
 * Searches Order Book's own customer table, independent of Loan
 * Book's — see api/httpOrderBookApi.ts's module docstring for why the
 * two features no longer share one.
 *
 * DEBOUNCED, 300ms, with a 2-character minimum before searching at
 * all. Without this, every keystroke fired its own request — typing
 * "Mandla" sent 6 separate GETs, one per letter, most of them for a
 * prefix the user was never going to stop on. The 2-character floor
 * also skips the least useful searches outright — a single letter
 * matches too broadly to be worth a round trip.
 *
 * REQUESTS ARE ACTUALLY CANCELLED, not just ignored. React Query
 * passes an AbortSignal into every queryFn call automatically, and
 * fires it the instant a query is superseded (query key changes
 * before the old one resolves — exactly what happens here every time
 * the debounced term changes). Wiring that signal through to
 * searchCustomers()'s existing signal param means a stale in-flight
 * request is genuinely aborted at the network layer, not left to run
 * to completion server-side and discarded client-side. Under real
 * traffic (many users typing quickly), that's the difference between
 * a superseded search still doing full backend/DB work for nothing
 * and it not — same debounce as before, this just makes the
 * cancellation real rather than cosmetic.
 */

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import type { Customer } from "../types";
import { searchCustomers } from "../api/orderBookApi";
import { orderBookKeys } from "./orderBookKeys";
import { useCurrentUserId } from "./useCurrentUserId";

const DEBOUNCE_MS = 300;
const MIN_SEARCH_LENGTH = 2;

export function useOrderCustomerSearch() {
  const userId = useCurrentUserId();
  const [term, setTerm] = useState("");
  const [debouncedTerm, setDebouncedTerm] = useState("");

  useEffect(() => {
    const handle = setTimeout(() => setDebouncedTerm(term), DEBOUNCE_MS);
    return () => clearTimeout(handle);
  }, [term]);

  const trimmed = debouncedTerm.trim();
  const shouldSearch = Boolean(userId) && trimmed.length >= MIN_SEARCH_LENGTH;

  const query = useQuery<Customer[]>({
    queryKey: orderBookKeys.customerSearch(userId, trimmed),
    queryFn: ({ signal }) => searchCustomers(trimmed, signal),
    enabled: shouldSearch,
  });

  const results = shouldSearch ? query.data ?? [] : [];

  return {
    term,
    setTerm,
    clear: () => {
      setTerm("");
      setDebouncedTerm("");
    },
    results,
    hasResults: results.length > 0,
    // Reflects the debounce window too, not just the network request —
    // the search bar shouldn't look idle while waiting out the 300ms
    // before the request even fires.
    isSearching: term.trim().length >= MIN_SEARCH_LENGTH && (term !== debouncedTerm || query.isFetching),
  };
}
