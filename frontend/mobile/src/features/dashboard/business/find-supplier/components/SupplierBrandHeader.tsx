import React, { useState } from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { CalendarDays, MapPin, Store } from "lucide-react-native";
import { VerifiedTick } from "@/components/ui/VerifiedTick";

import { FullScreenImageViewer } from "@/components/ui/FullScreenImageViewer";
import { InfoHint } from "@/components/ui/InfoHint";
import { SupplierActivityDot } from "./SupplierActivityDot";
import { showsAsVerified } from "@/constants/config";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import { palette } from "@/theme/colors";

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
  | "activity"
>;

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
  activity,
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
            trigger={<VerifiedTick size={18} />}
          />
        )}
      </View>

      {meta ? (
        <View style={styles.metaRow}>
          {(category || location) && <MapPin size={13} color={theme.colors.onSurfaceVariant} strokeWidth={2} />}
          <Text style={[styles.metaText, { color: theme.colors.onSurfaceVariant }]}>{meta}</Text>
        </View>
      ) : null}
      {/* Directly under the name: "are these people around" is a fact
          about the supplier, like the name itself, and a business
          shouldn't have to scroll to find it. Renders nothing unless
          the supplier switched sharing on. */}
      <SupplierActivityDot activity={activity} />

      {memberSince ? (
        <View style={styles.metaRow}>
          <CalendarDays size={13} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
          <Text style={[styles.metaText, { color: theme.colors.onSurfaceVariant }]}>
            On TruConnect since {memberSince}
          </Text>
        </View>
      ) : null}

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
