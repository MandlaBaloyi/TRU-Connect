import React from "react";

import { FeedSupplierList } from "../components/FeedSupplierList";
import { useFeedSuppliers } from "../hooks/useFeedDetail";
import { getCollectNearYou } from "../services/feedDetailService";

/**
 * Every supplier inside the collection radius, nearest first.
 *
 * A LIST, NOT A GRID: these are entities to choose between rather than
 * goods to compare, and each row carries a different kind of fact.
 *
 * STRICTLY DISTANCE-ORDERED, at every tier, forever. This is the only
 * surface in the app that prints the number it is sorted by, which is
 * exactly why it can never be tie-broken by anything else -- the reader
 * would be holding the contradiction (V2_17 Q5).
 */
export default function CollectNearYouScreen() {
  const feed = useFeedSuppliers("collect-near-you", getCollectNearYou);

  return (
    <FeedSupplierList
      title="Collect near you"
      feed={feed}
      emptyTitle={"No suppliers near you yet"}
      emptyBody={"Pin your shop on the map in your profile, and any supplier close enough to collect from will appear here."}
    />
  );
}
