import React from "react";

import { ListCard, StatusPill } from "@/components/lists/CardListUI";
import { EntityAvatar } from "@/components/ui/EntityAvatar";
import { showsAsVerified } from "@/constants/config";

import type { SupplierSearchResult } from "../types";

const VERIFICATION_TONE = { verified: "on", pending: "warning", unverified: "off" } as const;
const VERIFICATION_LABEL = { verified: "Verified", pending: "Pending", unverified: "Unverified" } as const;

interface Props {
  result: SupplierSearchResult;
  onPress: () => void;
}

/**
 * REDESIGNED AGAIN, this time back toward a row -- see this file's own
 * git history for the prior "shop tile" grid pivot. That grid had a
 * real, concrete problem this fixes structurally, not just
 * cosmetically: a supplier with no category/location yet (a normal,
 * expected state, not an error) produced a visibly SHORTER card next
 * to a taller one in the same row, since two cards had to pair up
 * side-by-side regardless of how much content each actually had. A
 * full-width row sizes itself to its own content -- nothing needs to
 * match its neighbour's height.
 *
 * Built on the SHARED ListCard (components/lists/CardListUI.tsx) --
 * now used identically by My Connections (see
 * shared/connections/components/MyConnectionsList.tsx) -- one visual
 * language for "this represents a supplier" everywhere it appears,
 * rather than search results and connections looking like two
 * unrelated features.
 *
 * photoUrl is real (see this feature's own types.ts) -- genuinely null
 * unless the supplier has actively chosen to show one AND this
 * business is allowed to see it; EntityAvatar's initials fallback is
 * the normal, expected state for most suppliers, not an error state.
 */
export function SupplierResultCard({ result, onPress }: Props) {
  const metaParts = [result.category, result.location].filter((part): part is string => Boolean(part));

  return (
    <ListCard
      title={result.businessName}
      badge={
        // ONLY THE POSITIVE CLAIM. "Unverified" is as much a statement
        // about a supplier as "Verified" is, and the curtain means a
        // business never sees an unverified one here anyway -- so the
        // absent case cannot occur, and rendering a pill for it would
        // be dead code that implies otherwise.
        showsAsVerified(result.verificationStatus) ? (
          <StatusPill
            label={VERIFICATION_LABEL[result.verificationStatus]}
            tone={VERIFICATION_TONE[result.verificationStatus]}
          />
        ) : undefined
      }
      // A single combined line ("Food & Beverages · Elim") rather than
      // two stacked ones -- reads as one fact ("what and where"), and
      // gracefully becomes just one part (or nothing at all) when the
      // supplier hasn't filled in one or both yet, without ever
      // leaving a visibly empty gap the way the old grid's separate
      // category/location blocks could.
      subtitle={metaParts.length > 0 ? metaParts.join(" · ") : undefined}
      onPress={onPress}
      icon={() => <EntityAvatar name={result.businessName} photoUrl={result.photoUrl} size={44} />}
    />
  );
}
