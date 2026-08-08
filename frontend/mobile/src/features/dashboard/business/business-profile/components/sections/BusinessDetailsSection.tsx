/**
 * Business Details — view-only summary for the landing screen. Edit
 * lives on its own screen now (my-business/business-details.tsx),
 * matching how every other "add/edit something real" flow in this app
 * works (Create Order is its own screen, not an inline form) — see
 * ORDER_BOOK feature for the precedent this now follows.
 */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import type { BusinessDetails } from "../../types";
import { BUSINESS_CATEGORY_LABELS, BUSINESS_TYPE_LABELS } from "../../types";
import { EditButton } from "../EditButton";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  details: BusinessDetails;
}

export function BusinessDetailsSection({ details }: Props) {
  const theme = useTheme();
  const router = useRouter();

  return (
    <View style={styles.viewMode}>
      <Text style={[styles.businessName, { color: theme.colors.onSurface }]}>{details.businessName}</Text>
      {(details.category || details.businessType) && (
        <Text style={[styles.metaLine, { color: theme.colors.onSurfaceVariant }]}>
          {[details.category && BUSINESS_CATEGORY_LABELS[details.category], details.businessType && BUSINESS_TYPE_LABELS[details.businessType]]
            .filter(Boolean)
            .join(" · ")}
        </Text>
      )}
      {details.description && (
        <Text style={[styles.description, { color: theme.colors.onSurface }]}>{details.description}</Text>
      )}
      <EditButton onPress={() => router.push("/business/my-business/business-details")} />
    </View>
  );
}

const styles = StyleSheet.create({
  viewMode: { gap: spacing.xs },
  businessName: { ...typography.h2 },
  metaLine: { ...typography.bodySmall },
  description: { ...typography.body },
});
