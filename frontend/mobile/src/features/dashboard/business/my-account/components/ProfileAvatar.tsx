/**
 * Profile avatar — image if one is approved, initials fallback
 * otherwise. Same initials-derivation idea as loan-book/order-book's
 * CustomerAvatar (deterministic colour from a seed), reimplemented
 * here rather than imported: that component models a CUSTOMER, this
 * one models the ACCOUNT HOLDER — different domain, same small idea,
 * not worth a cross-feature dependency for ~10 lines of logic.
 *
 * showCameraBadge is now SEPARATE from onPress (they used to be the
 * same thing) — the landing screen's avatar is tappable (goes to
 * Profile) but must NOT show the camera icon there, since that
 * implied "tap to change photo" and the actual photo control lives on
 * Profile now; showing it twice was a real duplicate control, not
 * just visual clutter.
 *
 * verified adds a small checkmark badge, bottom-left, opposite the
 * camera badge. Deliberately just an echo of the REAL, already-wired
 * verificationStatus — see this feature's own VerificationBadge
 * component for the full reasoning on why this doesn't invent a
 * second "photo verified" concept. Two states only: nothing, or the
 * checkmark — no partial/pending version on the avatar itself.
 */
import React from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { BadgeCheck, Camera } from "lucide-react-native";

import { palette } from "@/theme/colors";

const AVATAR_COLOURS = [palette.truePointBlue, palette.emeraldGreenDark, "#6B4E9E", "#B45309"];

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function colourFor(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  return AVATAR_COLOURS[hash % AVATAR_COLOURS.length];
}

interface Props {
  name: string;
  imageUri?: string | null;
  size?: number;
  onPress?: () => void;
  /** Defaults true when onPress is set, matching the previous
   *  behaviour everywhere except the landing screen, which now
   *  explicitly passes false. */
  showCameraBadge?: boolean;
  verified?: boolean;
}

export function ProfileAvatar({ name, imageUri, size = 88, onPress, showCameraBadge, verified = false }: Props) {
  const theme = useTheme();
  const shouldShowCameraBadge = showCameraBadge ?? Boolean(onPress);

  const content = imageUri ? (
    <Image source={{ uri: imageUri }} style={{ width: size, height: size, borderRadius: size / 2 }} />
  ) : (
    <View
      style={[
        styles.fallback,
        { width: size, height: size, borderRadius: size / 2, backgroundColor: colourFor(name) },
      ]}
    >
      <Text style={[styles.initials, { fontSize: size * 0.36 }]}>{getInitials(name)}</Text>
    </View>
  );

  return (
    <Pressable
      onPress={onPress}
      accessibilityRole={onPress ? "button" : "image"}
      accessibilityLabel={onPress ? "Edit profile" : "Profile photo"}
      style={styles.wrap}
    >
      {content}
      {verified && (
        <View style={[styles.verifiedBadge, { backgroundColor: theme.colors.secondary, borderColor: theme.colors.background }]}>
          <BadgeCheck size={14} color={palette.white} strokeWidth={2.4} />
        </View>
      )}
      {shouldShowCameraBadge && (
        <View style={[styles.cameraBadge, { backgroundColor: theme.colors.primary, borderColor: theme.colors.background }]}>
          <Camera size={14} color={palette.white} strokeWidth={2.2} />
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  wrap: { alignItems: "center", justifyContent: "center" },
  fallback: { alignItems: "center", justifyContent: "center" },
  initials: { color: palette.white, fontWeight: "700" },
  cameraBadge: {
    position: "absolute",
    right: -2,
    bottom: -2,
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 2,
    alignItems: "center",
    justifyContent: "center",
  },
  verifiedBadge: {
    position: "absolute",
    left: -2,
    bottom: -2,
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    alignItems: "center",
    justifyContent: "center",
  },
});
