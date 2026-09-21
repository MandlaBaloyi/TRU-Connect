import React from "react";

import { FeedProductGrid } from "../components/FeedProductGrid";
import { useFeedProducts } from "../hooks/useFeedDetail";
import { getLeftOff } from "../services/feedDetailService";

/**
 * Everything this shop opened and never ordered.
 *
 * WHY THE RAIL NEEDED A SCREEN AT ALL, and the general case for arrows
 * here: a shop that browses fifty products cannot reach the fiftieth by
 * scrolling a twelve-card shelf sideways. The rail is a preview of a
 * list, so there has to be a list.
 *
 * THE LIST IS NOT CAPPED PER SUPPLIER, unlike the rail. Twelve cards
 * are a recommendation and one wholesaler must not own them; a full
 * list is the shop's own browsing history, and hiding part of it
 * because one supplier happens to sell what they were looking at would
 * be the screen refusing the question it was opened to answer.
 *
 * IT SHRINKS AS THEY BUY, which is the design rather than a quirk: an
 * ordered product belongs to "Reorder what you need" and leaves here.
 * The empty state is therefore a GOOD outcome and says so.
 */
export default function LeftOffScreen() {
  const feed = useFeedProducts("left-off", getLeftOff);

  return (
    <FeedProductGrid
      title="Continue stocking up"
      feed={feed}
      emptyTitle={"Nothing left hanging"}
      emptyBody={"Products you open but do not order show up here, so you can come back to them."}
    />
  );
}
