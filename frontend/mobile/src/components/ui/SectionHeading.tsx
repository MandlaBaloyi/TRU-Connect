import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { InfoHint } from "@/components/ui/InfoHint";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * A section heading, with its explanation behind an ⓘ rather than in a
 * permanent grey paragraph underneath.
 *
 * WHY: the supplier profile had grown four such paragraphs, and
 * together they meant a supplier scrolled through more explanation
 * than actual profile. Each sentence was individually justified; the
 * total wasn't. The heading names the section, the ⓘ explains it, and
 * a supplier who already knows never pays for it.
 *
 * LIVES IN components/ui/ rather than in either feature. It started as
 * a private helper inside the supplier ProfileScreen; when the
 * visibility switches moved out of that screen and into Settings, the
 * headings had to move with them, and a settings feature folder
 * importing a private helper out of my-account would have been the
 * wrong direction entirely. Neutral ground instead.
 */
export function SectionHeading({ title, hint }: { title: string; hint?: string | string[] }) {
  const theme = useTheme();
  return (
    <View style={styles.row}>
      <Text style={[styles.title, { color: theme.colors.onSurfaceVariant }]}>{title}</Text>
      {hint && <InfoHint title={title} body={hint} size={15} />}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: spacing.xs, marginTop: spacing.sm },
  title: { ...typography.caption, fontWeight: "700", textTransform: "uppercase", letterSpacing: 0.5 },
});
