import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import QRCode from "react-native-qrcode-svg";

import { Note } from "@/components/lists/CardListUI";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useConnectCode } from "../hooks/useConnectCode";
import { useAccountProfile } from "../hooks/useAccountProfile";

/**
 * "My Code" tab — genuinely real QR rendering (see this file's own
 * caption for the honest scope note); the VALUE encoded is mock, see
 * accountService.ts's own note. Extracted out of what used to be the
 * whole QRCodeScreen so that screen can now switch between this and
 * ScanCodeTab, matching the My Code / Scan Code reference.
 */
export function MyCodeTab() {
  const theme = useTheme();
  const { connectCode, isLoading, regenerate, isRegenerating } = useConnectCode();
  const { summary } = useAccountProfile();

  const fullName = summary ? [summary.firstName, summary.lastName].filter(Boolean).join(" ") || summary.email : "";

  if (isLoading || !connectCode) {
    return (
      <View style={styles.centre}>
        <ActivityIndicator color={theme.colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.content}>
      <View style={[styles.card, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
        <Text style={[styles.name, { color: theme.colors.onSurface }]}>{fullName}</Text>
        {summary?.businessName && (
          <Text style={[styles.businessName, { color: theme.colors.onSurfaceVariant }]}>{summary.businessName}</Text>
        )}
        <View style={styles.qrWrap}>
          <QRCode value={`truconnect://connect/${connectCode.token}`} size={220} />
        </View>
      </View>

      <Text style={[styles.caption, { color: theme.colors.onSurfaceVariant }]}>
        A supplier can scan this to connect with you directly, without searching.
      </Text>

      <PrimaryButton onPress={() => regenerate()} loading={isRegenerating} disabled={isRegenerating}>
        Generate new code
      </PrimaryButton>

      <Note>
        If you generate a new code, anyone with your old one won't be able to use it to connect with you anymore.
      </Note>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingHorizontal: spacing.md, paddingBottom: spacing.xxl, gap: spacing.md },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  card: { alignItems: "center", borderRadius: radius.lg, borderWidth: 1, padding: spacing.lg, gap: spacing.xs },
  name: { ...typography.h2 },
  businessName: { ...typography.body },
  qrWrap: { marginTop: spacing.md, padding: spacing.md, backgroundColor: "#FFFFFF", borderRadius: radius.md },
  caption: { ...typography.bodySmall, textAlign: "center" },
});
