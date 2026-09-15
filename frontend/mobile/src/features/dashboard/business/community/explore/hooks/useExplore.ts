import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { getExplore } from "../services/exploreService";
import type { ExplorePage } from "../services/exploreService";

export const exploreKeys = {
  all: ["community-explore"] as const,
  byKind: (kind?: string) => [...exploreKeys.all, kind ?? "default"] as const,
};

/**
 * The explore screen's state: which kind is selected, and what that
 * returns.
 *
 * placeholderData KEEPS THE CHIPS ON SCREEN WHILE THE LIST RELOADS.
 * Without it the row of chips disappears on every tap and comes back a
 * moment later, so the control you just used vanishes underneath your
 * finger -- and since the chips come back in the SAME response as the
 * suppliers, this is the only way to keep them stable.
 *
 * NO PAGING, unlike the feed's see-all screens. The backend returns up
 * to PAGE_SIZE = 40 and reports the true total; a market with more than
 * forty wholesalers of one kind is a problem this app does not have
 * yet, and building offset paging against a list that short would be
 * machinery with nothing to carry. The count in the header tells the
 * truth in the meantime.
 */
export function useExplore(initialKind?: string) {
  const [kind, setKind] = useState<string | undefined>(initialKind);

  const query = useQuery<ExplorePage>({
    queryKey: exploreKeys.byKind(kind),
    queryFn: () => getExplore(kind),
    placeholderData: keepPreviousData,
  });

  return {
    kind,
    setKind,
    suppliers: query.data?.suppliers ?? [],
    kinds: query.data?.kinds ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    isError: query.isError,
    isRefetching: query.isRefetching,
    refetch: () => {
      void query.refetch();
    },
  };
}
