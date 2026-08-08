import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { User } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/** Placeholder only — My Account is not built yet. Real screen, real
 *  route, honestly says "coming soon" rather than being a dead link. */
export default function MyAccountScreen() {
  const theme = useTheme();
  return (
    <ScreenContainer>
      <View style={styles.centre}>
        <User size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />
        <Text style={[styles.title, { color: theme.colors.onSurface }]}>My Account</Text>
        <Text style={[styles.body, { color: theme.colors.onSurfaceVariant }]}>Coming soon.</Text>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center", gap: spacing.sm, padding: spacing.lg },
  title: { ...typography.h1 },
  body: { ...typography.body },
});
