import React, { useCallback, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { useTheme } from "react-native-paper";
import { KeyRound, ShieldCheck, Smartphone, MonitorSmartphone, History, Bell, Fingerprint } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { SecuritySection, SecurityCard, SecurityHero, StatusPill, formatWhen } from "../components/SecurityUI";
import { getSecurityOverview } from "../services/securityService";
import type { SecurityOverview } from "../types";
import { spacing } from "@/theme/spacing";

/**
 * Account Security landing screen.
 *
 * PROGRESSIVE DISCLOSURE (spec §4): this screen shows each area's
 * STATE, not its settings — every control lives one level down. That
 * keeps the first screen scannable ("is anything wrong?") instead of
 * an overwhelming wall of switches.
 *
 * Refetches on focus so returning from, say, enabling 2FA shows the
 * new state immediately rather than a stale one.
 */
export default function AccountSecurityScreen() {
  const router = useRouter();
  const theme = useTheme();
  const [overview, setOverview] = useState<SecurityOverview | null>(null);

  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      getSecurityOverview().then((data) => {
        if (!cancelled) setOverview(data);
      });
      return () => {
        cancelled = true;
      };
    }, [])
  );

  if (!overview) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  const go = (path: string) => () => router.push(path as any);
  const twoFactorLabel = overview.twoFactor.isEnabled ? "On" : "Off";

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <SecurityHero
          icon={<ShieldCheck size={28} color={theme.colors.primary} strokeWidth={1.8} />}
          title="Account Security"
          description="Everything that protects your account, in one place."
        />
        <SecuritySection title="Sign-in">
          <SecurityCard
            icon={(c) => <KeyRound size={20} color={c} />}
            label="Password"
            description={
              overview.password.lastChangedAt
                ? `Last changed ${formatWhen(overview.password.lastChangedAt)}`
                : "Never changed"
            }
            onPress={go("/business/security/password")}
          />
          <SecurityCard
            icon={(c) => <ShieldCheck size={20} color={c} />}
            label="Two-factor authentication"
            description="An extra step when signing in"
            status={<StatusPill label={twoFactorLabel} tone={overview.twoFactor.isEnabled ? "on" : "off"} />}
            onPress={go("/business/security/two-factor")}
          />
          <SecurityCard
            icon={(c) => <Fingerprint size={20} color={c} />}
            label="Biometric sign-in"
            description="Use your fingerprint or face"
            onPress={go("/business/security/biometrics")}
          />
        </SecuritySection>

        <SecuritySection title="Devices & activity">
          <SecurityCard
            icon={(c) => <Smartphone size={20} color={c} />}
            label="Trusted devices"
            description={`${overview.trustedDeviceCount} device${overview.trustedDeviceCount === 1 ? "" : "s"}`}
            onPress={go("/business/security/trusted-devices")}
          />
          <SecurityCard
            icon={(c) => <MonitorSmartphone size={20} color={c} />}
            label="Where you're signed in"
            description={`${overview.activeSessionCount} active session${overview.activeSessionCount === 1 ? "" : "s"}`}
            onPress={go("/business/security/active-sessions")}
          />
          <SecurityCard
            icon={(c) => <History size={20} color={c} />}
            label="Login activity"
            description="Recent sign-ins to your account"
            onPress={go("/business/security/login-activity")}
          />
          <SecurityCard
            icon={(c) => <Bell size={20} color={c} />}
            label="Security alerts"
            description="Important notices about your account"
            status={
              overview.unreadAlertCount > 0 ? (
                <StatusPill label={`${overview.unreadAlertCount} new`} tone="warning" />
              ) : undefined
            }
            onPress={go("/business/security/security-alerts")}
          />
        </SecuritySection>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.xl },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
});
