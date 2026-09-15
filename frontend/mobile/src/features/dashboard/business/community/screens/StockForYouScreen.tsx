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
      products={feed.products}
      total={feed.total}
      emptyTitle={"Tell us what you buy"}
      emptyBody={"Once we know what your shop stocks, this fills up with things you can actually order."}
      isLoading={feed.isLoading}
      isError={feed.isError}
      refetch={feed.refetch}
      isRefetching={feed.isRefetching}
      onEndReached={() => {
        if (feed.hasNextPage && !feed.isFetchingNextPage) feed.fetchNextPage();
      }}
      isFetchingNextPage={feed.isFetchingNextPage}
    />
  );
}
