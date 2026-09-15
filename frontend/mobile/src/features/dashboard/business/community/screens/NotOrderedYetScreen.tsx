import React from "react";

import { FeedSupplierList } from "../components/FeedSupplierList";
import { useFeedSuppliers } from "../hooks/useFeedDetail";
import { getNotOrderedYet } from "../services/feedDetailService";

/**
 * Every supplier in reach this shop has never bought from.
 *
 * THE LAST RAIL WITHOUT A SCREEN. The service, the endpoint and the
 * paging have existed since the see-all work; sections.py deliberately
 * withheld the chevron rather than ship an arrow that led nowhere, and
 * this is the screen that lets it have one.
 *
 * CONNECTED OR NOT, WHICH IS THE POINT OF THE RAIL. A connection that
 * stalled after the handshake and a supplier they have never met are
 * the same opportunity from here: somebody with stock, in reach, never
 * bought from. The ones they already know sort first -- the trust is
 * done, only the first order is missing.
 *
 * NOT FRAMED AS A FAILURE, on the screen any more than on the rail.
 * The empty state states a fact and offers a next action; anything
 * scolding would be the platform telling a shopkeeper off for how they
 * run their shop.
 */
export default function NotOrderedYetScreen() {
  const feed = useFeedSuppliers("not-ordered-yet", getNotOrderedYet);

  return (
    <FeedSupplierList
      suppliers={feed.suppliers}
      total={feed.total}
      emptyTitle="Nothing new in reach yet"
      emptyBody="You've ordered from every supplier we can see near you. Invite one you trade with offline, and they'll show up here."
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
