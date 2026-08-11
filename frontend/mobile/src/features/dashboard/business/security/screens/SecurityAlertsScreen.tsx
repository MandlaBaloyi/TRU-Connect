import React, { useEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Switch, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Bell, AlertTriangle, Info, ShieldAlert } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SecurityHero, formatWhen } from "../components/SecurityUI";
import { getSecurityAlerts, markAlertRead } from "../services/securityService";
import { useSecurityAlertPreference } from "../hooks/useSecurityAlertPreference";
import type { SecurityAlert } from "../types";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * Security alerts.
 *
 * REAL, PERSISTED TOGGLE — default OFF, per direct instruction. This
 * controls whether TruConnect notifies you about security alerts
 * OUTSIDE the app (once that delivery infrastructure exists). It does
 * NOT hide alerts from this screen either way: something that already
 * happened, like a blocked sign-in attempt, always stays visible here
 * regardless of the toggle — hiding a real security event from the one
 * place that shows it would defeat the point of the feature. See
 * hooks/useSecurityAlertPreference.ts for the full reasoning.
 */
export default function SecurityAlertsScreen() {
  const theme = useTheme();
  const [alerts, setAlerts] = useState<SecurityAlert[] | null>(null);
  const { isEnabled, isLoaded, setEnabled } = useSecurityAlertPreference();

  useEffect(() => {
    let cancelled = false;
    getSecurityAlerts().then((a) => {
      if (!cancelled) setAlerts(a);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleRead = async (alert: SecurityAlert) => {
    if (alert.isRead) return;
    await markAlertRead(alert.id);
    setAlerts(await getSecurityAlerts());
  };

  const iconFor = (severity: SecurityAlert["severity"], color: string) =>
    severity === "CRITICAL" ? (
      <ShieldAlert size={20} color={color} />
    ) : severity === "WARNING" ? (
      <AlertTriangle size={20} color={color} />
    ) : (
      <Info size={20} color={color} />
    );

  const toneFor = (severity: SecurityAlert["severity"]) =>
    severity === "INFO" ? theme.colors.onSurfaceVariant : theme.colors.error;

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <SecurityHero
          icon={<Bell size={28} color={theme.colors.primary} strokeWidth={1.8} />}
          title="Security alerts"
          description="Notices about your account, like a blocked sign-in attempt."
        />

        <View style={[styles.toggleRow, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
          <View style={styles.toggleText}>
            <Text style={[styles.toggleLabel, { color: theme.colors.onSurface }]}>Notify me about alerts</Text>
            <Text style={[styles.toggleDescription, { color: theme.colors.onSurfaceVariant }]}>
              Alerts always appear on this screen either way — this is about being notified outside the app.
            </Text>
          </View>
          <Switch
            value={isEnabled}
            onValueChange={setEnabled}
            disabled={!isLoaded}
            accessibilityLabel="Notify me about security alerts"
          />
        </View>

        {alerts === null ? (
          <View style={styles.centre}>
            <ActivityIndicator color={theme.colors.primary} />
          </View>
        ) : alerts.length === 0 ? (
          <EmptyState
            icon={<Bell size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
            message="No security alerts. We'll let you know here if anything needs your attention."
          />
        ) : (
          alerts.map((alert) => (
            <Pressable
              key={alert.id}
              onPress={() => handleRead(alert)}
              style={[
                styles.card,
                {
                  backgroundColor: alert.isRead ? theme.colors.surface : theme.colors.surfaceVariant,
                  borderColor: alert.isRead ? theme.colors.outlineVariant : toneFor(alert.severity),
                },
              ]}
              accessibilityRole="button"
              accessibilityLabel={alert.title}
            >
              <View style={styles.cardHeader}>
                {iconFor(alert.severity, toneFor(alert.severity))}
                <Text style={[styles.title, { color: theme.colors.onSurface }]}>{alert.title}</Text>
                {!alert.isRead && <View style={[styles.unreadDot, { backgroundColor: toneFor(alert.severity) }]} />}
              </View>
              <Text style={[styles.body, { color: theme.colors.onSurfaceVariant }]}>{alert.description}</Text>
              <Text style={[styles.when, { color: theme.colors.onSurfaceVariant }]}>{formatWhen(alert.occurredAt)}</Text>
            </Pressable>
          ))
        )}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.md },
  centre: { alignItems: "center", justifyContent: "center", paddingVertical: spacing.xl },
  toggleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    padding: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
    marginBottom: spacing.sm,
  },
  toggleText: { flex: 1, gap: 2 },
  toggleLabel: { ...typography.body, fontWeight: "700" },
  toggleDescription: { ...typography.bodySmall, lineHeight: 17 },
  card: { borderRadius: radius.lg, borderWidth: 1, padding: spacing.md, gap: spacing.xs },
  cardHeader: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  title: { ...typography.body, fontWeight: "700", flex: 1 },
  unreadDot: { width: 8, height: 8, borderRadius: 4 },
  body: { ...typography.bodySmall, lineHeight: 19 },
  when: { ...typography.bodySmall, opacity: 0.7, marginTop: 2 },
});
