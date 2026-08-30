import React from "react";
import { Image, StyleSheet, Text, View } from "react-native";

import { ListCard, StatusPill } from "@/components/lists/CardListUI";
import { palette } from "@/theme/colors";

import type { SupplierSearchResult } from "../types";

const VERIFICATION_TONE = { verified: "on", pending: "warning", unverified: "off" } as const;
const VERIFICATION_LABEL = { verified: "Verified", pending: "Pending", unverified: "Unverified" } as const;
const TILE_COLOURS = [palette.truePointBlue, palette.emeraldGreenDark, "#6B4E9E", "#B45309"];

function colourFor(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  return TILE_COLOURS[hash % TILE_COLOURS.length];
}

function initialsFor(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

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
 * business is allowed to see it; the initials-avatar fallback below is
 * the normal, expected state for most suppliers, not an error state.
 */
export function SupplierResultCard({ result, onPress }: Props) {
  const metaParts = [result.category, result.location].filter((part): part is string => Boolean(part));

  return (
    <ListCard
      title={result.businessName}
      badge={
        <StatusPill
          label={VERIFICATION_LABEL[result.verificationStatus]}
          tone={VERIFICATION_TONE[result.verificationStatus]}
        />
      }
      // A single combined line ("Food & Beverages · Elim") rather than
      // two stacked ones -- reads as one fact ("what and where"), and
      // gracefully becomes just one part (or nothing at all) when the
      // supplier hasn't filled in one or both yet, without ever
      // leaving a visibly empty gap the way the old grid's separate
      // category/location blocks could.
      subtitle={metaParts.length > 0 ? metaParts.join(" · ") : undefined}
      onPress={onPress}
      icon={() =>
        result.photoUrl ? (
          <Image source={{ uri: result.photoUrl }} style={styles.avatarImage} />
        ) : (
          <View style={[styles.avatarImage, styles.fallback, { backgroundColor: colourFor(result.businessName) }]}>
            <Text style={styles.fallbackText}>{initialsFor(result.businessName)}</Text>
          </View>
        )
      }
    />
  );
}

const styles = StyleSheet.create({
  avatarImage: { width: 44, height: 44, borderRadius: 22 },
  fallback: { alignItems: "center", justifyContent: "center" },
  fallbackText: { color: palette.white, fontWeight: "700", fontSize: 15 },
});
