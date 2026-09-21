import React from "react";

import { FeedProductGrid } from "../components/FeedProductGrid";
import { useFeedProducts } from "../hooks/useFeedDetail";
import { getStockForYou } from "../services/feedDetailService";

/**
 * The demand engine's full answer: what this shop buys, priced for
 * what it can spend, strongest need first.
 *
 * THE SAME RANKING THE RAIL PREVIEWED. Both read
 * feed_detail_service on the backend, so this screen cannot re-rank
 * what the rail showed -- which would be the first thing a reader
 * noticed and the last thing a test would.
 */
export default function StockForYouScreen() {
  const feed = useFeedProducts("stock-for-you", getStockForYou);

  return (
    <FeedProductGrid
      title="Stock for your shop"
      feed={feed}
      emptyTitle={"Nothing matched yet"}
      emptyBody={"Tell us what you stock and we will fill this with products from suppliers near you."}
    />
  );
}
