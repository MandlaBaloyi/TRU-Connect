import React from "react";

import { FeedProductGrid } from "../components/FeedProductGrid";
import { useFeedProducts } from "../hooks/useFeedDetail";
import { getMovingFast } from "../services/feedDetailService";

/**
 * Products selling faster than they usually do, in the categories this
 * shop buys.
 *
 * RECOMPUTED ON EVERY FETCH rather than pinned to when the screen
 * opened. A list whose whole claim is "right now" must not be a
 * snapshot of ten minutes ago, and pull-to-refresh has to mean
 * something here.
 */
export default function MovingFastScreen() {
  const feed = useFeedProducts("moving-fast", getMovingFast);

  return (
    <FeedProductGrid
      title="Popular with businesses"
      feed={feed}
      emptyTitle={"Nothing is moving yet"}
      emptyBody={"When other businesses start buying something faster than usual, it shows up here. Quiet weeks are normal."}
    />
  );
}
