import React from "react";
import { Text, StyleSheet, TextStyle } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

interface Props {
  /** "By continuing, you agree to TruConnect's" (landing) or
   *  "I agree to TruConnect's" (registration checkbox) — the leading
   *  words before the two clickable document names. Trailing space is
   *  added automatically. */
  lead: string;
  style?: TextStyle;
}

/**
 * Renders "<lead> Terms of Service and Privacy Policy." as one
 * sentence with the two document names as real tappable links,
 * pushing to the public (legal) route group (reachable pre-auth).
 * Used in all three places policies need to be reachable: the landing
 * screen, business registration, and supplier registration — one
 * component so the wording and behaviour can never drift between the
 * three.
 */
export function PolicyLinksText({ lead, style }: Props) {
  const router = useRouter();
  const theme = useTheme();
  const linkStyle = { color: theme.colors.primary, fontWeight: "700" as const };

  return (
    <Text style={[styles.base, { color: theme.colors.onSurfaceVariant }, style]}>
      {lead}{" "}
      <Text style={linkStyle} onPress={() => router.push("/(legal)/terms")} accessibilityRole="link">
        Terms of Service
      </Text>{" "}
      and{" "}
      <Text style={linkStyle} onPress={() => router.push("/(legal)/privacy-policy")} accessibilityRole="link">
        Privacy Policy
      </Text>
      .
    </Text>
  );
}

const styles = StyleSheet.create({
  base: { fontSize: 12, lineHeight: 18 },
});
