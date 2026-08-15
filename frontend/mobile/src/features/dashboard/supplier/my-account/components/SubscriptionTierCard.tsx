import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Check } from "lucide-react-native";

import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { StatusPill } from "@/components/lists/CardListUI";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import type { SubscriptionTierInfo } from "../types";

interface Props {
  tier: SubscriptionTierInfo;
  isCurrent: boolean;
  onUpgrade: () => void;
  isUpgrading: boolean;
}

export function SubscriptionTierCard({ tier, isCurrent, onUpgrade, isUpgrading }: Props) {
  const theme = useTheme();

  return (
    <View
      style={[
        styles.card,
        {
          backgroundColor: theme.colors.surface,
          borderColor: isCurrent ? theme.colors.primary : theme.colors.outlineVariant,
          borderWidth: isCurrent ? 2 : 1,
        },
      ]}
    >
      <View style={styles.header}>
        <Text style={[styles.name, { color: theme.colors.onSurface }]}>{tier.name}</Text>
        {isCurrent && <StatusPill label="Current plan" tone="on" />}
      </View>
      <Text style={[styles.price, { color: theme.colors.onSurfaceVariant }]}>{tier.priceLabel}</Text>

      <View style={styles.features}>
        {tier.features.map((feature) => (
          <View key={feature} style={styles.featureRow}>
            <Check size={16} color={theme.colors.secondary} strokeWidth={2.4} />
            <Text style={[styles.featureText, { color: theme.colors.onSurface }]}>{feature}</Text>
          </View>
        ))}
      </View>

      {!isCurrent && (
        <PrimaryButton onPress={onUpgrade} loading={isUpgrading} disabled={isUpgrading}>
          Upgrade to {tier.name}
        </PrimaryButton>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: radius.lg, padding: spacing.lg, gap: spacing.sm },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  name: { ...typography.h2 },
  price: { ...typography.body, fontWeight: "600" },
  features: { gap: spacing.xs, marginVertical: spacing.sm },
  featureRow: { flexDirection: "row", alignItems: "flex-start", gap: spacing.xs },
  featureText: { ...typography.bodySmall, flex: 1, lineHeight: 18 },
});
