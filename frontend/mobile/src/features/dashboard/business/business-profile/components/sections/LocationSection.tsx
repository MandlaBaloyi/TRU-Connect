/** Location — view-only summary. Edit lives on its own screen
 *  (my-business/location.tsx). */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import type { BusinessLocation, OperatingModel } from "../../types";
import { EditButton } from "../EditButton";
import { OPERATING_MODEL_LABELS, PROVINCE_LABELS } from "../../types";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  location: BusinessLocation;
  operatingModel: OperatingModel | undefined;
}

export function LocationSection({ location, operatingModel }: Props) {
  const theme = useTheme();
  const router = useRouter();

  const summary = [location.cityOrTown, location.province && PROVINCE_LABELS[location.province]]
    .filter(Boolean)
    .join(", ");

  return (
    <View style={styles.viewMode}>
      {summary && <Text style={[styles.summaryText, { color: theme.colors.onSurface }]}>{summary}</Text>}
      {operatingModel && (
        <Text style={[styles.metaLine, { color: theme.colors.onSurfaceVariant }]}>{OPERATING_MODEL_LABELS[operatingModel]}</Text>
      )}
      {location.physicalAddress && (
        <Text style={[styles.metaLine, { color: theme.colors.onSurfaceVariant }]}>{location.physicalAddress}</Text>
      )}
      <EditButton onPress={() => router.push("/business/my-business/location")} />
    </View>
  );
}

const styles = StyleSheet.create({
  viewMode: { gap: spacing.xs },
  summaryText: { ...typography.body, fontWeight: "600" },
  metaLine: { ...typography.bodySmall },
});
