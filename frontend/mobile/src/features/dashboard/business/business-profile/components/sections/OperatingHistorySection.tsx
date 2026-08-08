import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import type { OperatingHistoryInfo } from "../../types";
import { EditButton } from "../EditButton";
import { OPERATING_HISTORY_LABELS } from "../../types";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  history: OperatingHistoryInfo;
}

export function OperatingHistorySection({ history }: Props) {
  const theme = useTheme();
  const router = useRouter();
  return (
    <View style={styles.viewMode}>
      <Text style={[styles.value, { color: theme.colors.onSurface }]}>
        {history.yearsOperating ? OPERATING_HISTORY_LABELS[history.yearsOperating] : "Not set"}
      </Text>
      <EditButton onPress={() => router.push("/business/my-business/operating-history")} />
    </View>
  );
}

const styles = StyleSheet.create({
  viewMode: { gap: spacing.xs },
  value: { ...typography.body },
});
