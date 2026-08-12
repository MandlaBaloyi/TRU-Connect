/**
 * Profile avatar — image if one is approved, initials fallback
 * otherwise. Same initials-derivation idea as loan-book/order-book's
 * CustomerAvatar (deterministic colour from a seed), reimplemented
 * here rather than imported: that component models a CUSTOMER, this
 * one models the ACCOUNT HOLDER — different domain, same small idea,
 * not worth a cross-feature dependency for ~10 lines of logic.
 */
import React from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Camera } from "lucide-react-native";

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
}

export function ProfileAvatar({ name, imageUri, size = 88, onPress }: Props) {
  const theme = useTheme();

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
      accessibilityLabel={onPress ? "Change profile photo" : "Profile photo"}
      style={styles.wrap}
    >
      {content}
      {onPress && (
        <View style={[styles.badge, { backgroundColor: theme.colors.primary, borderColor: theme.colors.background }]}>
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
  badge: {
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
});
