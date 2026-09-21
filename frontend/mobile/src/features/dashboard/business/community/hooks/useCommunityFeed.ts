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
 *
 * ADDING A SECTION TYPE MEANS EDITING TWO FILES, AND BOTH FAIL
 * SILENTLY IF YOU FORGET. This switch and FeedSectionView's switch are
 * independent gates on the same question, and each one's default drops
 * the section without a word -- which is correct for an OLD app
 * meeting a NEW server, and merciless when the two are shipped
 * together. EXPLORE_KINDS was added to the renderer and not to this
 * filter: the server sent it, the renderer could draw it, and it never
 * arrived, with no error anywhere and a clean rebuild changing
 * nothing. If you are here adding a case, go and check the other file
 * before you run the app.
 */
function isWorthRendering(section: FeedSection): boolean {
  switch (section.type) {
    case "PRODUCT_RAIL":
      return section.products.length >= MIN_ITEMS_PER_RAIL;
    case "SUPPLIER_RAIL":
      // ONE CARD IS ENOUGH FOR THE INVITES RAIL, and the server says so
      // explicitly. invited_suppliers' own docstring: "ONE CARD IS
      // ENOUGH HERE, unlike every other rail on this screen...
      // 'Thabo Beverages joined because you invited them' is a
      // complete thought on its own, and padding it would be the
      // mistake." This blanket floor was silently overruling that --
      // the server sent the rail, the app binned it, and the single
      // most invested thing a shopkeeper can do went back to having no
      // reply. The exemption is by id because the rule is per-rail;
      // every other supplier rail IS discovery and still needs three.
      if (section.id === "invited-suppliers") return section.suppliers.length > 0;
      return section.suppliers.length >= MIN_ITEMS_PER_RAIL;
    case "SUPPLIER_AVATARS":
      return section.suppliers.length > 0;
    case "CATEGORY_CHIPS":
      return section.categories.length > 0;
    case "PROMO":
    case "SPONSORED_SUPPLIER":
      return true;
    case "EXPLORE_KINDS":
      // NOT A RAIL EITHER — a set of doorways, and one door is a
      // complete offer rather than a thin shelf. The server already
      // returns nothing at all when no kind has a supplier behind it.
      return section.kinds.length > 0;
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
