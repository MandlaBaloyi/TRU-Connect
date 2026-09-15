import React from "react";
import { Image, StyleSheet, Text, View } from "react-native";

import { palette } from "@/theme/colors";

/**
 * The one "circular photo, or coloured initials when there's no photo"
 * avatar used everywhere a business or supplier is represented in a
 * row or a header — search results
 * (find-supplier/components/SupplierResultCard.tsx), My Connections
 * (shared/connections/components/MyConnectionsList.tsx), and the
 * social-style feature headers
 * (navigation/EntityHeaderTitle.tsx). The initials-fallback colour is
 * derived from the name so the same entity always gets the same
 * colour, and a missing photo is the NORMAL state (most suppliers
 * haven't uploaded one), never an error look.
 *
 * Extracted from SupplierResultCard, which owned this logic inline
 * first.
 */

const TILE_COLOURS = [palette.truePointBlue, palette.emeraldGreenDark, "#6B4E9E", "#B45309"];

/** EXPORTED so a card can paint a LARGER surface in the same colour
 *  this avatar would have used — see SupplierCard's cover fallback.
 *  The promise that "the same entity always gets the same colour" only
 *  holds if there is exactly one function deciding it, which is why
 *  the cover reuses this rather than deriving its own. */
export function entityColour(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  return TILE_COLOURS[hash % TILE_COLOURS.length];
}

export function entityInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export function EntityAvatar({
  name,
  photoUrl,
  size = 44,
}: {
  name: string;
  photoUrl?: string | null;
  size?: number;
}) {
  const dimension = { width: size, height: size, borderRadius: size / 2 };

  if (photoUrl) {
    return <Image source={{ uri: photoUrl }} style={dimension} />;
  }

  return (
    <View style={[dimension, styles.fallback, { backgroundColor: entityColour(name) }]}>
      <Text style={[styles.fallbackText, { fontSize: Math.round(size * 0.34) }]}>{entityInitials(name)}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  fallback: { alignItems: "center", justifyContent: "center" },
  fallbackText: { color: palette.white, fontWeight: "700" },
});
