import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { ImportPreviewSummary } from "../types";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  summary: ImportPreviewSummary;
  hasZip: boolean;
}

function StatBlock({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <View style={styles.stat}>
      <Text style={[styles.statValue, { color }]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

export function ImportSummaryCard({ summary, hasZip }: Props) {
  const theme = useTheme();

  return (
    <View style={[styles.card, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outline }]}>
      <View style={styles.statsRow}>
        <StatBlock label="Total rows" value={summary.totalRows} color={theme.colors.onSurface} />
        <StatBlock label="Ready" value={summary.validRows} color={theme.colors.primary} />
        <StatBlock label="Errors" value={summary.errorRows} color={theme.colors.error} />
      </View>
      {hasZip && summary.totalImageReferences > 0 && (
        <Text style={[styles.imagesLine, { color: theme.colors.onSurfaceVariant }]}>
          Images: {summary.matchedImages} / {summary.totalImageReferences} matched
          {summary.missingImages > 0 ? ` — ${summary.missingImages} not found in ZIP` : ""}
        </Text>
      )}
      {!hasZip && summary.totalImageReferences > 0 && (
        <Text style={[styles.imagesLine, { color: theme.colors.error }]}>
          {summary.totalImageReferences} image reference{summary.totalImageReferences === 1 ? "" : "s"} in your
          file, but no ZIP was uploaded.
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { borderWidth: 1, borderRadius: radius.lg, padding: spacing.md, gap: spacing.sm },
  statsRow: { flexDirection: "row", justifyContent: "space-around" },
  stat: { alignItems: "center", gap: 2 },
  statValue: { ...typography.h1, fontWeight: "800" },
  statLabel: { ...typography.caption },
  imagesLine: { ...typography.bodySmall, textAlign: "center" },
});
