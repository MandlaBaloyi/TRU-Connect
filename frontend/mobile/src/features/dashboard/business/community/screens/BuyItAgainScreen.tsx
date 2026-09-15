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
      products={feed.products}
      total={feed.total}
      emptyTitle={"Nothing to buy again yet"}
      emptyBody={"Once you have placed an order, everything in it shows up here so you can restock in a tap."}
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
