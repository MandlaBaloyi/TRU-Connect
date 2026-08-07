/**
 * useLoanSearch — customer search for the picker and the list header.
 *
 * Debounced INSIDE the hook, not in the screen, so every consumer gets
 * identical behaviour and no screen can accidentally fire a query per
 * keystroke on a low-end device (Doc 02 §2.1: design against the
 * realistic low end).
 */

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { searchCustomers } from "../api/loanBookApi";
import { loanBookKeys } from "./loanBookKeys";
import { useCurrentUserId } from "./useCurrentUserId";

const SEARCH_DEBOUNCE_MS = 250;

export function useLoanSearch(initialTerm = "") {
  const userId = useCurrentUserId();
  const [term, setTerm] = useState(initialTerm);
  const [debouncedTerm, setDebouncedTerm] = useState(initialTerm);

  // MUST be useEffect, not useMemo: useMemo does not run the cleanup
  // function it returns, so a useMemo version would leave every
  // keystroke's timer running and fire them all — the exact opposite of
  // debouncing, and invisible until you watch a search field on a slow
  // phone.
  useEffect(() => {
    const handle = setTimeout(() => setDebouncedTerm(term), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(handle);
  }, [term]);

  const query = useQuery({
    queryKey: loanBookKeys.customerSearch(userId, debouncedTerm),
    queryFn: () => searchCustomers(debouncedTerm),
    enabled: Boolean(userId),
  });

  return {
    term,
    setTerm,
    clear: () => setTerm(""),
    results: query.data ?? [],
    isSearching: query.isLoading,
    hasResults: (query.data?.length ?? 0) > 0,
    isEmpty: !query.isLoading && (query.data?.length ?? 0) === 0 && debouncedTerm.trim().length > 0,
  };
}