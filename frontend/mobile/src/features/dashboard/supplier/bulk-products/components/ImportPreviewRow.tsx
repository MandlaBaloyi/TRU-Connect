import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { AlertCircle, CheckCircle2 } from "lucide-react-native";

import type { ParsedImportRow } from "../types";
import { CATEGORY_OPTIONS } from "../../products/types";
import { formatCents } from "../../products/services/productMapper";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  row: ParsedImportRow;
}

export function ImportPreviewRow({ row }: Props) {
  const theme = useTheme();
  const isValid = row.errors.length === 0;
  const displayName = row.name ?? row.raw.name ?? "(no name)";
  const categoryLabel = row.category ? CATEGORY_OPTIONS.find((o) => o.value === row.category)?.label : null;

  return (
    <View style={styles.row}>
      <View style={styles.rowHeader}>
        {isValid ? (
          <CheckCircle2 size={16} color={theme.colors.primary} strokeWidth={2} />
        ) : (
          <AlertCircle size={16} color={theme.colors.error} strokeWidth={2} />
        )}
        <Text style={[styles.rowNumber, { color: theme.colors.onSurfaceVariant }]}>Row {row.rowNumber}</Text>
        <Text style={[styles.rowName, { color: theme.colors.onSurface }]} numberOfLines={1}>
          {displayName}
        </Text>
      </View>

      {isValid ? (
        <Text style={[styles.rowMeta, { color: theme.colors.onSurfaceVariant }]}>
          {categoryLabel} • {row.priceCents !== null ? formatCents(row.priceCents) : ""} • {row.quantity ?? 0} in
          stock
        </Text>
      ) : (
        <View style={styles.errorList}>
          {row.errors.map((error, index) => (
            <Text key={index} style={[styles.errorText, { color: theme.colors.error }]}>
              • {error.message}
            </Text>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { paddingVertical: spacing.sm, gap: 4 },
  rowHeader: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  rowNumber: { ...typography.caption },
  rowName: { ...typography.body, fontWeight: "600", flexShrink: 1 },
  rowMeta: { ...typography.bodySmall, marginLeft: 24 },
  errorList: { marginLeft: 24, gap: 2 },
  errorText: { ...typography.bodySmall },
});
