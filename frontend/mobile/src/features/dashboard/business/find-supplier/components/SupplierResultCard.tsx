import React from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { MapPin } from "lucide-react-native";

import { StatusPill } from "@/components/lists/CardListUI";
import { palette } from "@/theme/colors";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

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
 * Redesigned per direct product feedback — was a horizontal list row,
 * now a "shop tile": name above, image below, the whole card tapping
 * through toward that supplier's products. Grid-friendly (meant to
 * render 2-up, see FindSupplierScreen.tsx's own layout), not a
 * full-width row.
 *
 * photoUrl is real now (see this feature's own types.ts) — genuinely
 * null unless the supplier has actively chosen to show one AND this
 * business is allowed to see it; the initials-tile fallback below is
 * the normal, expected state for most suppliers, not an error state.
 *
 * file.txt §4 still applies: the masked-identifier confirmation line
 * from the old row design is dropped here on purpose — a visual tile
 * grid doesn't have room for it without cluttering the card, and the
 * match itself (query -> this result) is already the confirmation;
 * the full profile screen still shows richer detail after tapping.
 */
export function SupplierResultCard({ result, onPress }: Props) {
  const theme = useTheme();

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant, opacity: pressed ? 0.85 : 1 },
      ]}
      accessibilityRole="button"
      accessibilityLabel={`View ${result.businessName}'s products`}
    >
      <View style={styles.header}>
        <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={1}>
          {result.businessName}
        </Text>
        <StatusPill
          label={VERIFICATION_LABEL[result.verificationStatus]}
          tone={VERIFICATION_TONE[result.verificationStatus]}
        />
      </View>

      {result.photoUrl ? (
        <Image source={{ uri: result.photoUrl }} style={styles.image} />
      ) : (
        <View style={[styles.image, styles.fallback, { backgroundColor: colourFor(result.businessName) }]}>
          <Text style={styles.fallbackText}>{initialsFor(result.businessName)}</Text>
        </View>
      )}

      <View style={styles.metaBlock}>
        {result.category && (
          <Text style={[styles.meta, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
            {result.category}
          </Text>
        )}
        {result.location && (
          <View style={styles.locationRow}>
            <MapPin size={11} color={theme.colors.onSurfaceVariant} />
            <Text style={[styles.meta, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
              {result.location}
            </Text>
          </View>
        )}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    width: "48%",
    padding: spacing.sm,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.xs,
  },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: spacing.xs },
  name: { ...typography.bodySmall, fontWeight: "700", flexShrink: 1 },
  image: { width: "100%", aspectRatio: 1, borderRadius: radius.md },
  fallback: { alignItems: "center", justifyContent: "center" },
  fallbackText: { color: palette.white, fontWeight: "700", fontSize: 28 },
  metaBlock: { gap: 2 },
  meta: { ...typography.bodySmall },
  locationRow: { flexDirection: "row", alignItems: "center", gap: 4 },
});
