import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import type { SupplierInfo } from "../../types";
import { EditButton } from "../EditButton";
import { SUPPLIER_SOURCE_LABELS } from "../../types";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  supplierInfo: SupplierInfo;
}

export function SupplierInfoSection({ supplierInfo }: Props) {
  const theme = useTheme();
  const router = useRouter();
  return (
    <View style={styles.viewMode}>
      <Text style={[styles.value, { color: theme.colors.onSurface }]}>
        {supplierInfo.sources.length > 0 ? supplierInfo.sources.map((s) => SUPPLIER_SOURCE_LABELS[s]).join(", ") : "Not set"}
      </Text>
      <EditButton onPress={() => router.push("/business/my-business/suppliers")} />
    </View>
  );
}

const styles = StyleSheet.create({
  viewMode: { gap: spacing.xs },
  value: { ...typography.body },
});
