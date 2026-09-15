import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { EntityAvatar } from "@/components/ui/EntityAvatar";
import { SupplierName } from "@/components/ui/SupplierName";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { FeedSupplier } from "../../types";

export const AVATAR_TILE_WIDTH = 72;

/**
 * A supplier as a circular logo with their name under it -- the
 * compact "your suppliers" row.
 *
 * WHY A SEPARATE SHAPE FROM SupplierCard rather than a smaller
 * variant of it. This row answers a different question: not "who
 * should I look at" but "take me back to the ones I already use".
 * That is recognition, not evaluation, so it shows the least possible
 * information -- a logo and a name -- and fits five or six on screen
 * instead of one and a half. A business returning to reorder should
 * reach their supplier in one tap without reading anything.
 *
 * NO META LINE HERE ON PURPOSE. Delivery terms and minimums matter
 * when choosing between suppliers; they are noise when you already
 * know which one you want.
 *
 * THE ACTIVITY DOT is the one exception, because it changes the
 * decision cheaply: a supplier who was online minutes ago is likely to
 * answer today. Only rendered when the supplier opted into sharing it
 * -- the gate is the field being null, so this cannot leak by
 * forgetting a flag.
 */
export function SupplierAvatarTile({
  supplier,
  onPress,
}: {
  supplier: FeedSupplier;
  onPress: () => void;
}) {
  const theme = useTheme();
  const isOnline = isRecentlyActive(supplier.lastActiveAt);

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.tile, { opacity: pressed ? 0.85 : 1 }]}
      accessibilityRole="button"
      accessibilityLabel={supplier.businessName}
    >
      <View>
        <EntityAvatar name={supplier.businessName} photoUrl={supplier.businessImageUrl} size={58} />
        {isOnline && (
          <View
            style={[
              styles.dot,
              { backgroundColor: theme.colors.secondary, borderColor: theme.colors.background },
            ]}
          />
        )}
      </View>
      <SupplierName
        name={supplier.businessName}
        verificationStatus={supplier.verificationStatus}
        style={[styles.name, { color: theme.colors.onSurface }]}
        containerStyle={styles.nameRow}
        numberOfLines={2}
        tickSize={11}
      />
    </Pressable>
  );
}

/** Within the last 15 minutes. Deliberately coarse: the heartbeat
 *  behind last_active is throttled (core/decorators), so anything
 *  finer would claim precision the data does not have. */
function isRecentlyActive(lastActiveAt: string | null): boolean {
  if (!lastActiveAt) return false;
  const seen = new Date(lastActiveAt).getTime();
  if (Number.isNaN(seen)) return false;
  return Date.now() - seen < 15 * 60 * 1000;
}

const styles = StyleSheet.create({
  tile: { width: AVATAR_TILE_WIDTH, alignItems: "center", gap: spacing.xs },
  dot: {
    position: "absolute",
    right: 1,
    bottom: 1,
    width: 14,
    height: 14,
    borderRadius: 7,
    borderWidth: 2.5,
  },
  name: { ...typography.caption, fontSize: 11, lineHeight: 14, textAlign: "center" },
  // Centred, because this tile stacks a name under a round avatar
  // rather than running a row left to right like every other card.
  nameRow: { justifyContent: "center" },
});
