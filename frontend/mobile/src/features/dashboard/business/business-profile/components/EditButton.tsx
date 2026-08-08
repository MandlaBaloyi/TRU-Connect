import React from "react";
import { Pressable, StyleSheet, Text } from "react-native";
import { useTheme } from "react-native-paper";
import { Pencil } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  onPress: () => void;
  label?: string;
}

/** A real, visible button — not a small text link. Per direct
 *  feedback: the old "Edit" text link was too easy to miss; this is
 *  a bordered pill with an icon, bigger touch target, and enough
 *  visual weight to read as the primary action on each card. */
export function EditButton({ onPress, label = "Edit" }: Props) {
  const theme = useTheme();
  return (
    <Pressable
      onPress={onPress}
      style={[styles.button, { borderColor: theme.colors.primary }]}
      accessibilityRole="button"
      accessibilityLabel={label}
    >
      <Pencil size={15} color={theme.colors.primary} strokeWidth={2.4} />
      <Text style={[styles.label, { color: theme.colors.primary }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    gap: 6,
    borderWidth: 1.5,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.md,
    minHeight: 40,
    marginTop: spacing.sm,
  },
  label: { ...typography.body, fontWeight: "700" },
});
