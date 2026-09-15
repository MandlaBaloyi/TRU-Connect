import React from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { EntityAvatar } from "@/components/ui/EntityAvatar";
import { VerifiedTick } from "@/components/ui/VerifiedTick";
import { showsAsVerified } from "@/constants/config";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { supplierMetaLine } from "./supplierMeta";
import type { FeedSupplier } from "../../types";

/**
 * The one paid slot in For You, as its own card.
 *
 * WHY THIS EXISTS AT ALL, rather than reusing SupplierCard. The
 * sponsored section used to render a SupplierCard at
 * SUPPLIER_CARD_WIDTH + PRODUCT_TILE_WIDTH -- roughly 360px -- and a
 * component designed as a 240px rail tile does not become a banner by
 * being told it is wider. Its 120px cover band stretched into a large
 * empty rectangle, which is the block Mandla saw and reasonably read
 * as "the sponsored card is broken".
 *
 * A FULL-WIDTH SLOT IS A DIFFERENT SHAPE FROM A RAIL TILE. A tile is
 * scanned sideways in a row of peers and leads with an image because
 * the image is how you tell six of them apart. This one has no peers
 * and is not being scanned -- it is the only card on its row -- so it
 * leads with the NAME and spends its width on the meta line a tile has
 * to truncate. Horizontal, logo left, the facts right.
 *
 * THE LABEL IS NOT IN HERE, and that is deliberate. It comes from the
 * server, on the section, and FeedSectionView renders it above this
 * card -- so a card can never be rendered without one by a future
 * caller who forgets. Paid placement that reads as an organic
 * recommendation is the fastest way to lose the trust this platform is
 * built on, and disclosure is not optional under advertising rules
 * either.
 *
 * NO COVER IMAGE, EVER, even when the supplier has one. At this width
 * a cover is a billboard, and the difference between "promoted" and
 * "advertisement" is exactly how much visual weight money can buy. The
 * logo is enough to recognise a brand; the rest of the card is facts
 * the shop can act on.
 */
export function SponsoredSupplierCard({
  supplier,
  onPress,
}: {
  supplier: FeedSupplier;
  onPress: () => void;
}) {
  const theme = useTheme();
  const meta = supplierMetaLine(supplier);

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        {
          backgroundColor: theme.colors.surface,
          borderColor: theme.colors.outlineVariant,
          opacity: pressed ? 0.85 : 1,
        },
      ]}
      accessibilityRole="button"
      accessibilityLabel={`Sponsored. ${supplier.businessName}. ${meta}`}
    >
      {supplier.businessImageUrl ? (
        <Image source={{ uri: supplier.businessImageUrl }} style={styles.logo} resizeMode="cover" />
      ) : (
        <EntityAvatar name={supplier.businessName} photoUrl={null} size={56} />
      )}

      <View style={styles.body}>
        <View style={styles.nameRow}>
          <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={1}>
            {supplier.businessName}
          </Text>
          {showsAsVerified(supplier.verificationStatus) && <VerifiedTick size={14} />}
        </View>

        {supplier.category ? (
          <Text style={[styles.line, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
            {supplier.category}
            {supplier.location ? ` · ${supplier.location}` : ""}
          </Text>
        ) : null}

        {/* TWO LINES HERE, WHERE THE TILE ALLOWS ONE. "Delivers · Min
            R500 · 3.2 km · 14 businesses connected" is four facts, and
            a 240px tile silently drops three of them. The width this
            slot was sold is spent on showing them rather than on a
            bigger picture. */}
        {meta ? (
          <Text style={[styles.line, { color: theme.colors.onSurfaceVariant }]} numberOfLines={2}>
            {meta}
          </Text>
        ) : null}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    padding: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
  },
  logo: { width: 56, height: 56, borderRadius: 28 },
  body: { flex: 1, gap: 2 },
  nameRow: { flexDirection: "row", alignItems: "center", gap: 4 },
  name: { ...typography.body, fontWeight: "700", flexShrink: 1 },
  line: { ...typography.bodySmall, fontSize: 12 },
});
