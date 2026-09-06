import React from "react";
import { ActivityIndicator, Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { BadgeCheck, Camera } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import { palette } from "@/theme/colors";

import { ProfileAvatar } from "./ProfileAvatar";

/**
 * The social-media-style profile header shared by the supplier's
 * Profile (edit) screen and the My Account landing screen -- one
 * source of truth so the cover, the overlapping avatar, and the
 * name treatment (business name first, personal name under it) stay
 * identical on both.
 *
 * `editable` toggles the affordances: on the edit screen the cover
 * shows an "Edit/Add cover" pill, the avatar shows a camera badge, and
 * an upload spinner can overlay either image; on the landing screen
 * both images just navigate to the edit screen.
 */
interface Props {
  /** Primary line -- the business name (falls back to personal name). */
  displayName: string;
  /** Secondary line -- the person's own name, shown only when it
   *  differs from displayName. */
  secondaryName?: string | null;
  coverUri: string | null;
  avatarUri: string | null;
  verified: boolean;
  bio?: string | null;
  editable?: boolean;
  /** "profile" | "cover" while that image is uploading (edit screen). */
  busySlot?: "profile" | "cover" | null;
  onCoverPress: () => void;
  onAvatarPress: () => void;
}

const COVER_HEIGHT = 158;
const AVATAR_OVERLAP = 46;

export function ProfileHeader({
  displayName,
  secondaryName,
  coverUri,
  avatarUri,
  verified,
  bio,
  editable = false,
  busySlot = null,
  onCoverPress,
  onAvatarPress,
}: Props) {
  const theme = useTheme();
  const showSecondary = Boolean(secondaryName && secondaryName !== displayName);

  return (
    <View style={styles.header}>
      <Pressable
        onPress={onCoverPress}
        disabled={busySlot === "cover"}
        style={({ pressed }) => [
          styles.coverWrap,
          { backgroundColor: theme.colors.surfaceVariant, opacity: pressed ? 0.9 : 1 },
        ]}
        accessibilityRole="button"
        accessibilityLabel={coverUri ? "Cover photo" : "Add a cover photo"}
      >
        {coverUri ? (
          <Image source={{ uri: coverUri }} style={styles.coverImage} resizeMode="cover" />
        ) : (
          <View style={styles.coverPlaceholder}>
            <Camera size={22} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
            <Text style={[styles.coverPlaceholderText, { color: theme.colors.onSurfaceVariant }]}>
              {editable ? "Add a cover photo" : "No cover photo yet"}
            </Text>
          </View>
        )}

        {editable && (
          <View style={styles.coverBadge}>
            <Camera size={13} color={palette.white} strokeWidth={2.2} />
            <Text style={styles.coverBadgeText}>{coverUri ? "Edit cover" : "Add cover"}</Text>
          </View>
        )}

        {busySlot === "cover" && (
          <View style={styles.imageBusyOverlay}>
            <ActivityIndicator color={palette.white} />
          </View>
        )}
      </Pressable>

      <View style={styles.avatarRow}>
        <View style={[styles.avatarRing, { backgroundColor: theme.colors.background }]}>
          <ProfileAvatar
            name={displayName}
            imageUri={avatarUri}
            size={92}
            onPress={onAvatarPress}
            showCameraBadge={editable}
            verified={verified}
          />
          {busySlot === "profile" && (
            <View style={[styles.imageBusyOverlay, styles.avatarBusyOverlay]}>
              <ActivityIndicator color={palette.white} />
            </View>
          )}
        </View>
      </View>

      <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={1}>
        {displayName}
      </Text>
      {showSecondary && (
        <Text style={[styles.subName, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
          {secondaryName}
        </Text>
      )}
      {verified && (
        <View style={styles.verifiedRow}>
          <BadgeCheck size={15} color={theme.colors.secondary} strokeWidth={2.4} />
          <Text style={[styles.verifiedText, { color: theme.colors.secondary }]}>Verified supplier</Text>
        </View>
      )}
      {bio ? (
        <Text style={[styles.bio, { color: theme.colors.onSurfaceVariant }]} numberOfLines={3}>
          {bio}
        </Text>
      ) : null}
      {editable && (
        <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>Tap a photo to change or view it</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  header: { alignItems: "center", paddingBottom: spacing.sm },
  coverWrap: { width: "100%", height: COVER_HEIGHT, overflow: "hidden" },
  coverImage: { width: "100%", height: "100%" },
  coverPlaceholder: { flex: 1, alignItems: "center", justifyContent: "center", gap: spacing.xs },
  coverPlaceholderText: { ...typography.bodySmall, fontWeight: "600" },
  coverBadge: {
    position: "absolute",
    right: spacing.md,
    bottom: spacing.sm,
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: radius.pill,
    backgroundColor: "rgba(0,0,0,0.55)",
  },
  coverBadgeText: { ...typography.caption, color: palette.white, fontWeight: "700" },
  imageBusyOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(0,0,0,0.35)",
  },
  avatarBusyOverlay: { borderRadius: radius.pill },
  avatarRow: { marginTop: -AVATAR_OVERLAP },
  avatarRing: { padding: 4, borderRadius: radius.pill },
  name: { ...typography.h1, fontWeight: "700", marginTop: spacing.sm, paddingHorizontal: spacing.md, textAlign: "center" },
  subName: { ...typography.body, fontWeight: "700", marginTop: 2, paddingHorizontal: spacing.md, textAlign: "center" },
  verifiedRow: { flexDirection: "row", alignItems: "center", gap: 5, marginTop: spacing.xs },
  verifiedText: { ...typography.bodySmall, fontWeight: "700" },
  bio: { ...typography.bodySmall, textAlign: "center", marginTop: spacing.xs, lineHeight: 19, paddingHorizontal: spacing.lg },
  hint: { ...typography.caption, marginTop: spacing.xs },
});
