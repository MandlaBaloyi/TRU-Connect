/**
 * CustomerAvatar — initials in a coloured circle.
 * Identical logic to loan-book's CustomerAvatar (same seed -> colour
 * hash), kept as this feature's own copy — see types.ts file docstring.
 * Using the SAME hash function means a customer shared between Loan
 * Book and Order Book shows the same avatar colour in both places.
 */

import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { palette } from "@/theme/colors";
import { typography } from "@/theme/typography";

const AVATAR_COLOURS = [
  palette.truePointBlue,
  palette.emeraldGreenDark,
  "#6B4E9E",
  "#B45309",
  "#0E7490",
  "#9F1239",
];

export function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function colourFor(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  }
  return AVATAR_COLOURS[hash % AVATAR_COLOURS.length];
}

interface Props {
  name: string;
  seed?: string;
  size?: number;
}

export function CustomerAvatar({ name, seed, size = 44 }: Props) {
  const background = colourFor(seed ?? name);
  return (
    <View
      style={[
        styles.avatar,
        { width: size, height: size, borderRadius: size / 2, backgroundColor: background },
      ]}
      accessibilityElementsHidden
      importantForAccessibility="no"
    >
      <Text style={[styles.initials, { fontSize: size * 0.36 }]}>{getInitials(name)}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  avatar: { alignItems: "center", justifyContent: "center" },
  initials: { ...typography.h2, color: palette.white, fontWeight: "600" },
});
