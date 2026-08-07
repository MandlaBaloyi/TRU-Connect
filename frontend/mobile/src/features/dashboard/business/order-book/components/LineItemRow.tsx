import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { X } from "lucide-react-native";

import { formatCents } from "../services/orderMapper";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  description: string;
  quantity: number;
  unitPrice: number;
  lineTotal: number;
  onRemove?: () => void;
}

export function LineItemRow({ description, quantity, unitPrice, lineTotal, onRemove }: Props) {
  const theme = useTheme();
  return (
    <View style={styles.row}>
      <View style={styles.body}>
        <Text style={[styles.description, { color: theme.colors.onSurface }]} numberOfLines={2}>
          {description}
        </Text>
        <Text style={[styles.meta, { color: theme.colors.onSurfaceVariant }]}>
          {quantity} × {formatCents(unitPrice)}
        </Text>
      </View>
      <Text style={[styles.total, { color: theme.colors.onSurface }]}>{formatCents(lineTotal)}</Text>
      {onRemove && (
        <Pressable onPress={onRemove} hitSlop={12} accessibilityRole="button" accessibilityLabel={`Remove ${description}`}>
          <X size={18} color={theme.colors.onSurfaceVariant} />
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: spacing.sm, paddingVertical: spacing.sm, minHeight: 44 },
  body: { flex: 1, gap: 2 },
  description: { ...typography.body },
  meta: { ...typography.bodySmall },
  total: { ...typography.body, fontWeight: "600" },
});
