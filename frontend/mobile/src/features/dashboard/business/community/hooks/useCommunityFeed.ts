import { useQuery } from "@tanstack/react-query";

import { getCommunityFeed } from "../services/communityFeedService";
import { MIN_ITEMS_PER_RAIL, type FeedSection } from "../types";

/**
 * The Community feed, filtered down to sections worth rendering.
 *
 * THE THIN-RAIL RULE IS APPLIED HERE, not in each component. A rail
 * holding one product looks worse than no rail: it reads as a broken
 * shelf rather than a short one, and a new business -- who has the
 * fewest connections and the least order history -- is exactly who
 * would see the most of them. Same "silence is the honest answer"
 * rule the track record already follows.
 *
 * DONE IN THE APP RATHER THAN TRUSTED FROM THE SERVER on purpose. The
 * server will apply its own minimums, but this is the last line before
 * a user sees it, and a half-empty shelf is the kind of thing that
 * slips through a ranking change nobody re-tested.
 *
 * CHIPS AND PROMOS ARE EXEMPT -- neither is a rail. A promo is one
 * card and complete on its own; a chip row of two categories is still
 * a usable chip row.
 */
function isWorthRendering(section: FeedSection): boolean {
  switch (section.type) {
    case "PRODUCT_RAIL":
      return section.products.length >= MIN_ITEMS_PER_RAIL;
    case "SUPPLIER_RAIL":
      return section.suppliers.length >= MIN_ITEMS_PER_RAIL;
    case "SUPPLIER_AVATARS":
      return section.suppliers.length > 0;
    case "CATEGORY_CHIPS":
      return section.categories.length > 0;
    case "PROMO":
    case "SPONSORED_SUPPLIER":
      return true;
    default:
      // An unknown section type from a newer server. Dropped silently
      // rather than crashed on -- see types.ts on why the server must
      // be free to ship a section this build has never heard of.
      return false;
  }
}

export function useCommunityFeed() {
  const query = useQuery({
    queryKey: ["community", "feed"],
    queryFn: getCommunityFeed,
  });

  return {
    sections: (query.data?.sections ?? []).filter(isWorthRendering),
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    isRefetching: query.isRefetching,
  };
}
