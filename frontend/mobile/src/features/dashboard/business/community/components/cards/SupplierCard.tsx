import React from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { BadgeCheck, Check } from "lucide-react-native";

import { EntityAvatar } from "@/components/ui/EntityAvatar";
import { showsAsVerified } from "@/constants/config";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { supplierMetaLine } from "./supplierMeta";
import type { FeedSupplier } from "../../types";

export const SUPPLIER_CARD_WIDTH = 240;

/**
 * A supplier, as a card in a rail: cover image, name, and the one
 * honest meta line (see supplierMeta.ts for what is in it and what is
 * deliberately not).
 *
 * THE COVER FALLS BACK TO THE LOGO, THEN TO INITIALS, and both
 * fallbacks are designed rather than tolerated. Most suppliers on this
 * platform today have uploaded neither -- a card that only looks right
 * with a professional cover photo would look broken for the majority
 * of a catalogue built by informal wholesalers on their phones. The
 * initials block is the same one used in search results and
 * connection lists, so an unphotographed supplier is consistently
 * recognisable rather than consistently empty.
 *
 * "CONNECTED" IS A STATE, NOT AN ACTION. The badge says where this
 * business already stands; it is never a button. Connecting is a real
 * decision with a request and an approval behind it, and it belongs on
 * the supplier's own profile where the terms are visible -- not as a
 * one-tap action on a card someone is scrolling past.
 */
export function SupplierCard({
  supplier,
  onPress,
  width = SUPPLIER_CARD_WIDTH,
}: {
  supplier: FeedSupplier;
  onPress: () => void;
  width?: number;
}) {
  const theme = useTheme();
  const cover = supplier.coverImageUrl ?? supplier.businessImageUrl;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, { width, opacity: pressed ? 0.85 : 1 }]}
      accessibilityRole="button"
      accessibilityLabel={`${supplier.businessName}. ${supplierMetaLine(supplier)}`}
    >
      <View style={[styles.coverWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
        {cover ? (
          <Image source={{ uri: cover }} style={styles.cover} resizeMode="cover" />
        ) : (
          <View style={styles.coverFallback}>
            <EntityAvatar name={supplier.businessName} photoUrl={null} size={56} />
          </View>
        )}

        {supplier.isConnected && (
          <View style={[styles.connectedPill, { backgroundColor: theme.colors.secondaryContainer }]}>
            <Check size={11} color={theme.colors.secondary} strokeWidth={3} />
            <Text style={[styles.connectedText, { color: theme.colors.secondary }]}>Connected</Text>
          </View>
        )}
      </View>

      <View style={styles.body}>
        <View style={styles.nameRow}>
          <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={1}>
            {supplier.businessName}
          </Text>
          {showsAsVerified(supplier.verificationStatus) && (
            <BadgeCheck size={14} color={theme.colors.primary} strokeWidth={2.4} />
          )}
        </View>

        {supplier.category ? (
          <Text style={[styles.category, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
            {supplier.category}
            {supplier.location ? ` · ${supplier.location}` : ""}
          </Text>
        ) : null}

        <Text style={[styles.meta, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
          {supplierMetaLine(supplier)}
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { gap: spacing.sm },
  coverWrap: {
    height: 120,
    borderRadius: radius.md,
    overflow: "hidden",
    justifyContent: "center",
    alignItems: "center",
  },
  cover: { width: "100%", height: "100%" },
  coverFallback: { alignItems: "center", justifyContent: "center" },
  connectedPill: {
    position: "absolute",
    top: spacing.sm,
    left: spacing.sm,
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    borderRadius: radius.pill,
  },
  connectedText: { ...typography.caption, fontWeight: "800", fontSize: 10 },
  body: { gap: 1 },
  nameRow: { flexDirection: "row", alignItems: "center", gap: 4 },
  name: { ...typography.body, fontWeight: "700", flexShrink: 1 },
  category: { ...typography.bodySmall, fontSize: 12 },
  meta: { ...typography.bodySmall, fontSize: 12 },
});
