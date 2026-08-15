import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { ChevronRight, Store } from "lucide-react-native";

import { formatWhen } from "@/components/lists/CardListUI";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { SupplierRequestSummary } from "../types";

interface Props {
  request: SupplierRequestSummary;
  onPress: () => void;
}

/** Mirrors supplier/customer-requests/components/CustomerRequestCard.tsx. */
export function SupplierRequestCard({ request, onPress }: Props) {
  const theme = useTheme();

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant, opacity: pressed ? 0.85 : 1 },
      ]}
      accessibilityRole="button"
      accessibilityLabel={`${request.businessName} wants to connect`}
    >
      <View style={[styles.iconWrap, { backgroundColor: theme.colors.primaryContainer }]}>
        <Store size={20} color={theme.colors.primary} />
      </View>
      <View style={styles.body}>
        <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={1}>
          {request.businessName}
        </Text>
        <Text style={[styles.meta, { color: theme.colors.onSurfaceVariant }]}>
          Wants to connect · {formatWhen(request.requestedAt)}
        </Text>
      </View>
      <ChevronRight size={18} color={theme.colors.onSurfaceVariant} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    padding: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
  },
  iconWrap: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center" },
  body: { flex: 1, gap: 2 },
  name: { ...typography.body, fontWeight: "700" },
  meta: { ...typography.bodySmall },
});
