import React from "react";

import { FeedProductGrid } from "../components/FeedProductGrid";
import { useFeedProducts } from "../hooks/useFeedDetail";
import { getBuyItAgain } from "../services/feedDetailService";

/**
 * Everything this shop has ever ordered, most recent first.
 *
 * NOT CAPPED PER SUPPLIER AT ANY LENGTH, unlike every other product
 * screen here. It is their own confirmed history: a wholesaler
 * appearing often is a fact about their trading, not domination, and
 * the recency order is information that interleaving would destroy
 * (V2_17 Q3).
 */
export default function BuyItAgainScreen() {
  const feed = useFeedProducts("buy-it-again", getBuyItAgain);

  return (
    <FeedProductGrid
      title="Reorder what you need"
      feed={feed}
      emptyTitle={"Nothing to reorder yet"}
      emptyBody={"Once you have placed an order, everything you bought shows up here so you can restock it in a tap."}
    />
  );
}
