/**
 * Debounced search — waits for the business to stop typing before
 * querying, so this doesn't fire a request per keystroke once it's
 * wired to a real, rate-limited backend endpoint (types.ts's contract
 * notes this is rate-limited per business_id). Debouncing here is
 * also just good UX regardless of backend, so it's built in from the
 * start rather than retrofitted.
 */
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { searchSuppliers } from "../services/supplierSearchService";

const DEBOUNCE_MS = 400;

export function useSupplierSearch(query: string) {
  const [debounced, setDebounced] = useState(query);

  useEffect(() => {
    const handle = setTimeout(() => setDebounced(query), DEBOUNCE_MS);
    return () => clearTimeout(handle);
  }, [query]);

  const trimmed = debounced.trim();

  const result = useQuery({
    queryKey: ["findSupplier", "search", trimmed],
    queryFn: () => searchSuppliers(trimmed),
    enabled: trimmed.length >= 2,
  });

  return {
    results: result.data ?? [],
    isSearching: result.isFetching,
    isError: result.isError,
    hasQuery: trimmed.length >= 2,
    // True only once a real (debounced) search has resolved with zero
    // rows — lets the screen distinguish "haven't searched yet" from
    // "genuinely no match" without a flash of the wrong empty state
    // while typing.
    isEmpty: result.isSuccess && trimmed.length >= 2 && result.data.length === 0,
  };
}
