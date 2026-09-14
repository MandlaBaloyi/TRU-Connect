import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { VerifiedTick } from "@/components/ui/VerifiedTick";

import { EntityAvatar } from "@/components/ui/EntityAvatar";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * A social-media-style feature-header title: a small avatar + the
 * entity's real name (+ a verified tick, only when genuinely
 * verified). Passed as `headerTitle` to FeatureHeader so the top bar
 * of a supplier's brand profile / stock catalogue reads "MacMan
 * Businesses" and "MacMan Businesses Stock" instead of the generic
 * "Supplier" / "Stock Catalogue" — a business needs to be certain, at
 * a glance, that this is THEIR supplier and THEIR stock.
 *
 * The tick rule mirrors SupplierBrandHeader exactly: a tick when
 * VERIFIED, nothing otherwise — never an "Unverified"/"Pending" label.
 *
 * `subtitle` puts a second, quieter line under the name (WhatsApp's
 * "name / last seen", Instagram's "name / category"). It exists for a
 * REAL reason, not decoration: the catalogue screen originally jammed
 * the context into the name itself ("MacMan Businesses Stock"), which
 * truncated to "MacMan Businesses St…" the moment the bar also held an
 * avatar, a cart icon and the ⋮ menu — losing the one word that gave
 * the suffix meaning. Splitting it across two lines keeps the business
 * name whole (the part that has to be recognisable) and moves the
 * "which screen is this" part to where it can be small.
 */
export function EntityHeaderTitle({
  name,
  subtitle,
  photoUrl,
  verified = false,
  onPress,
}: {
  name: string;
  subtitle?: string;
  photoUrl?: string | null;
  verified?: boolean;
  onPress?: () => void;
}) {
  const theme = useTheme();

  const content = (
    <>
      <EntityAvatar name={name} photoUrl={photoUrl} size={subtitle ? 32 : 28} />
      <View style={styles.textColumn}>
        <View style={styles.nameRow}>
          <Text
            style={[subtitle ? styles.nameCompact : styles.name, { color: theme.colors.onSurface }]}
            numberOfLines={1}
            ellipsizeMode="tail"
          >
            {name}
          </Text>
          {verified && <VerifiedTick size={15} />}
        </View>
        {subtitle && (
          <Text
            style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}
            numberOfLines={1}
            ellipsizeMode="tail"
          >
            {subtitle}
          </Text>
        )}
      </View>
    </>
  );

  // Tapping the name/photo opens that entity's profile -- the
  // convention every social and marketplace app shares (the header
  // identity is always a link back to whose page this is). Only
  // pressable when a destination was actually supplied; the profile
  // screen itself passes none, since it IS the destination.
  if (!onPress) {
    return <View style={styles.row}>{content}</View>;
  }

  return (
    <Pressable
      onPress={onPress}
      hitSlop={8}
      style={({ pressed }) => [styles.row, { opacity: pressed ? 0.6 : 1 }]}
      accessibilityRole="button"
      accessibilityLabel={`View ${name}'s profile`}
    >
      {content}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: spacing.xs, flexShrink: 1 },
  textColumn: { flexShrink: 1 },
  nameRow: { flexDirection: "row", alignItems: "center", gap: 4, flexShrink: 1 },
  name: { ...typography.h2, flexShrink: 1 },
  // Slightly tighter than h2 so name + subtitle together still clear
  // FeatureHeader's own 56px row without crowding it.
  nameCompact: { ...typography.body, fontWeight: "700", flexShrink: 1 },
  subtitle: { ...typography.bodySmall, fontSize: 12, lineHeight: 15 },
});
