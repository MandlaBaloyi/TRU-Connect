import React, { useState } from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { BadgeCheck, CalendarDays, MapPin, Store } from "lucide-react-native";

import { FullScreenImageViewer } from "@/components/ui/FullScreenImageViewer";
import { InfoHint } from "@/components/ui/InfoHint";
import { showsAsVerified } from "@/constants/config";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import { palette } from "@/theme/colors";

import { CATEGORY_OPTIONS } from "../../../supplier/products/types";
import type { SupplierProfilePreview } from "../types";

/**
 * The brand header a business sees on a supplier's profile -- the
 * conversion moment (per the Relationship Intelligence plan). Same
 * social-media visual language as the supplier's own ProfileHeader: a
 * full-bleed cover with the business photo overlapping its lower edge,
 * business name, then a muted meta line.
 *
 * The cover and business photo are PUBLIC brand assets (backend returns
 * them ungated) -- tapping either opens a fullscreen viewer. No
 * verification "Unverified"/"Pending" text ever: a tick + "Verified"
 * shows ONLY when the supplier is genuinely verified, nothing
 * otherwise.
 */
type Props = Pick<
  SupplierProfilePreview,
  | "businessName"
  | "category"
  | "location"
  | "verificationStatus"
  | "memberSince"
  | "description"
  | "businessImageUrl"
  | "coverImageUrl"
  | "photoUrl"
  | "stockedCategories"
>;

const MAX_CATEGORY_CHIPS = 4;

/** The human label for a raw ProductCategory value, falling back to the
 *  raw value so an unknown//new category degrades to something readable
 *  rather than vanishing. */
function labelForCategory(value: string): string {
  return CATEGORY_OPTIONS.find((option) => option.value === value)?.label ?? value;
}

const COVER_HEIGHT = 158;
const AVATAR_OVERLAP = 46;

export function SupplierBrandHeader({
  businessName,
  category,
  location,
  verificationStatus,
  memberSince,
  description,
  businessImageUrl,
  coverImageUrl,
  photoUrl,
  stockedCategories,
}: Props) {
  const theme = useTheme();
  const [viewerUri, setViewerUri] = useState<string | null>(null);

  const avatarUri = businessImageUrl ?? photoUrl;
  const isVerified = showsAsVerified(verificationStatus);

  const meta = [category, location].filter(Boolean).join("  ·  ");

  return (
    <View style={styles.header}>
      <Pressable
        onPress={() => coverImageUrl && setViewerUri(coverImageUrl)}
        style={({ pressed }) => [
          styles.coverWrap,
          { backgroundColor: theme.colors.surfaceVariant, opacity: pressed ? 0.9 : 1 },
        ]}
        accessibilityRole={coverImageUrl ? "button" : "none"}
        accessibilityLabel={coverImageUrl ? "View cover photo" : undefined}
      >
        {coverImageUrl && <Image source={{ uri: coverImageUrl }} style={styles.coverImage} resizeMode="cover" />}
      </Pressable>

      <View style={styles.avatarRow}>
        <Pressable
          onPress={() => avatarUri && setViewerUri(avatarUri)}
          style={[styles.avatarRing, { backgroundColor: theme.colors.background }]}
          accessibilityRole={avatarUri ? "button" : "image"}
          accessibilityLabel={avatarUri ? "View business photo" : "Business photo"}
        >
          {avatarUri ? (
            <Image source={{ uri: avatarUri }} style={styles.avatar} />
          ) : (
            <View style={[styles.avatar, styles.avatarFallback, { backgroundColor: theme.colors.primaryContainer }]}>
              <Store size={34} color={theme.colors.primary} strokeWidth={1.8} />
            </View>
          )}
        </Pressable>
      </View>

      <View style={styles.nameRow}>
        <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={2}>
          {businessName}
        </Text>
        {/* The tick alone. A green "Verified supplier" line used to sit
            under this, which meant the same fact was asserted THREE
            times on one screen -- tick in the top bar, tick here, and
            that line. Once the tick is understood the text is
            repetition, and it was pushing the description and products
            further down for nothing. */}
        {isVerified && (
          <InfoHint
            title="Verified supplier"
            body={[
              "TruConnect has checked this supplier's business details before letting them trade on the platform.",
              "It is not a guarantee about price, stock or delivery — those are between you and the supplier. Always check an order before you pay.",
            ]}
            accessibilityLabel="What does the verified tick mean?"
            trigger={<BadgeCheck size={18} color={theme.colors.secondary} strokeWidth={2.4} />}
          />
        )}
      </View>

      {meta ? (
        <View style={styles.metaRow}>
          {(category || location) && <MapPin size={13} color={theme.colors.onSurfaceVariant} strokeWidth={2} />}
          <Text style={[styles.metaText, { color: theme.colors.onSurfaceVariant }]}>{meta}</Text>
        </View>
      ) : null}
      {memberSince ? (
        <View style={styles.metaRow}>
          <CalendarDays size={13} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
          <Text style={[styles.metaText, { color: theme.colors.onSurfaceVariant }]}>
            On TruConnect since {memberSince}
          </Text>
        </View>
      ) : null}

      {/* WHAT THEY ACTUALLY STOCK, from their real products -- not a
          self-described category. Sits directly under the description
          on purpose: a supplier's own bio drifts (a real case here was
          a bio about fragrances above a shop full of cold drinks and
          chips), and these chips correct it without contradicting
          anyone. Capped so a supplier with a dozen categories doesn't
          push the products off screen. */}
      {stockedCategories.length > 0 && (
        <View style={styles.categoryRow}>
          {stockedCategories.slice(0, MAX_CATEGORY_CHIPS).map((category) => (
            <View key={category} style={[styles.categoryChip, { backgroundColor: theme.colors.surfaceVariant }]}>
              <Text style={[styles.categoryChipText, { color: theme.colors.onSurfaceVariant }]}>
                {labelForCategory(category)}
              </Text>
            </View>
          ))}
          {stockedCategories.length > MAX_CATEGORY_CHIPS && (
            <View style={[styles.categoryChip, { backgroundColor: theme.colors.surfaceVariant }]}>
              <Text style={[styles.categoryChipText, { color: theme.colors.onSurfaceVariant }]}>
                +{stockedCategories.length - MAX_CATEGORY_CHIPS}
              </Text>
            </View>
          )}
        </View>
      )}

      {description ? (
        <Text style={[styles.description, { color: theme.colors.onSurface }]}>{description}</Text>
      ) : null}

      <FullScreenImageViewer visible={viewerUri !== null} uri={viewerUri} onClose={() => setViewerUri(null)} />
    </View>
  );
}

const styles = StyleSheet.create({
  header: { alignItems: "center", paddingBottom: spacing.sm },
  coverWrap: { width: "100%", height: COVER_HEIGHT, overflow: "hidden" },
  coverImage: { width: "100%", height: "100%" },
  avatarRow: { marginTop: -AVATAR_OVERLAP },
  avatarRing: { padding: 4, borderRadius: radius.pill },
  avatar: { width: 92, height: 92, borderRadius: 46 },
  avatarFallback: { alignItems: "center", justifyContent: "center" },
  nameRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    marginTop: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  name: { ...typography.h1, fontWeight: "700", textAlign: "center", flexShrink: 1 },
  categoryRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "center",
    gap: spacing.xs,
    marginTop: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  categoryChip: { paddingHorizontal: spacing.sm, paddingVertical: 4, borderRadius: radius.pill },
  categoryChipText: { ...typography.bodySmall, fontWeight: "600", fontSize: 12 },
  metaRow: { flexDirection: "row", alignItems: "center", gap: 5, marginTop: spacing.xs, paddingHorizontal: spacing.md },
  metaText: { ...typography.bodySmall },
  description: {
    ...typography.body,
    lineHeight: 21,
    textAlign: "center",
    marginTop: spacing.sm,
    paddingHorizontal: spacing.lg,
  },
});
