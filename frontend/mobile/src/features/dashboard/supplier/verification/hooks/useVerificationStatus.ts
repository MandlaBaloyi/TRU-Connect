/**
 * The supplier's own visibility state, cached for the whole session.
 *
 * STALE TIME IS LONG ON PURPOSE. Verification changes roughly once in
 * an account's lifetime, and it is decided by a person at a terminal
 * rather than by anything the supplier does in the app -- so polling
 * it would spend requests on a value that almost never moves.
 *
 * WHICH MEANS THE GOOD NEWS CAN ARRIVE LATE, and that is the one real
 * cost: a supplier approved while their app is open keeps seeing the
 * banner until the query refetches. Acceptable because the refetch
 * happens whenever the app returns to the foreground, and because the
 * opposite error -- a supplier told they are live when they are not --
 * is the one that would actually hurt.
 */
import { useQuery } from "@tanstack/react-query";

import { getMyVerificationStatus } from "../services/verificationService";

export const verificationStatusKey = ["supplier", "verification", "me"] as const;

export function useVerificationStatus() {
  return useQuery({
    queryKey: verificationStatusKey,
    queryFn: getMyVerificationStatus,
    staleTime: 5 * 60 * 1000,
  });
}
