import React from "react";
import { Image, StyleSheet, Text, View } from "react-native";

import { ListCard } from "@/components/lists/CardListUI";
import { palette } from "@/theme/colors";

import type { BusinessSearchResult } from "../types";

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
  result: BusinessSearchResult;
  onPress: () => void;
}

/**
 * Mirrors business/find-supplier/components/SupplierResultCard.tsx's
 * own redesign exactly -- same ListCard row, same reasoning. No
 * verification pill here, same as before (BusinessSearchResult has no
 * such field).
 */
export function BusinessResultCard({ result, onPress }: Props) {
  const metaParts = [result.category, result.location].filter((part): part is string => Boolean(part));

  return (
    <ListCard
      title={result.businessName}
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
