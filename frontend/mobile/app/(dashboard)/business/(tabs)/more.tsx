import React, { Fragment } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { ChevronRight, LogOut, User, Store, ShieldCheck, Settings as SettingsIcon } from "lucide-react-native";
import Constants from "expo-constants";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { useLogout } from "@/features/auth/hooks/useAuth";
import { palette } from "@/theme/colors";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * More tab — flat divider-separated rows (no card container), each
 * with an icon, bold title, subtitle, and chevron. Home stays
 * untouched; this screen only.
 *
 * My Account, My Business, Account Security, and Settings each have
 * their own isolated feature folder + route (same separation as Order
 * Book/Loan Book) — all four navigate for real.
 */
const ROWS: { key: string; label: string; subtitle: string; route: string; icon: React.ReactNode }[] = [
  {
    key: "my-account",
    label: "My Account",
    subtitle: "Manage your personal information",
    route: "/business/my-account",
    icon: <User size={22} color={palette.truePointBlue} strokeWidth={2.2} />,
  },
  {
    key: "my-business",
    label: "My Business",
    subtitle: "Manage your business information",
    route: "/business/my-business",
    icon: <Store size={22} color={palette.emeraldGreen} strokeWidth={2.2} />,
  },
  {
    key: "security",
    label: "Account security",
    subtitle: "Protect your account and security",
    route: "/business/security",
    icon: <ShieldCheck size={22} color={palette.truePointBlue} strokeWidth={2.2} />,
  },
  {
    key: "settings",
    label: "Settings",
    subtitle: "Manage your app preferences",
    route: "/business/settings",
    icon: <SettingsIcon size={22} color={palette.truePointBlue} strokeWidth={2.2} />,
  },
];

export default function BusinessMore() {
  const router = useRouter();
  const theme = useTheme();
  const logout = useLogout();

  return (
    <ScreenContainer offsetForBrandTopBar>
      <View style={styles.content}>
        <View style={[styles.list, { borderColor: theme.colors.outline }]}>
          {ROWS.map((row, index) => (
            <Fragment key={row.key}>
              <Pressable
                onPress={() => router.push(row.route as any)}
                style={styles.row}
                accessibilityRole="button"
                accessibilityLabel={row.label}
              >
                <View style={[styles.iconWrap, { backgroundColor: theme.colors.surfaceVariant }]}>{row.icon}</View>
                <View style={styles.textWrap}>
                  <Text style={[styles.label, { color: theme.colors.onSurface }]}>{row.label}</Text>
                  <Text style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}>{row.subtitle}</Text>
                </View>
                <ChevronRight size={20} color={theme.colors.onSurfaceVariant} />
              </Pressable>
              {index < ROWS.length - 1 && <View style={[styles.divider, { backgroundColor: theme.colors.outline }]} />}
            </Fragment>
          ))}
        </View>

        <Text style={[styles.version, { color: theme.colors.onSurfaceVariant }]}>
          Version {Constants.expoConfig?.version ?? "1.0.0"}
        </Text>

        <View style={[styles.divider, { backgroundColor: theme.colors.outline }]} />

        <Pressable
          onPress={() => logout.mutate()}
          disabled={logout.isPending}
          style={styles.signOutRow}
          accessibilityRole="button"
          accessibilityLabel="Sign out"
        >
          <LogOut size={16} color={theme.colors.primary} strokeWidth={2.2} />
          <Text style={[styles.signOutText, { color: theme.colors.primary }]}>
            {logout.isPending ? "Signing out…" : "Sign out"}
          </Text>
        </Pressable>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { gap: spacing.lg, paddingTop: spacing.none, paddingBottom: spacing.lg },
  list: { borderTopWidth: StyleSheet.hairlineWidth, borderBottomWidth: StyleSheet.hairlineWidth },
  row: { flexDirection: "row", alignItems: "center", gap: spacing.md, minHeight: 64, paddingVertical: spacing.sm },
  iconWrap: { width: 40, height: 40, borderRadius: 10, alignItems: "center", justifyContent: "center" },
  textWrap: { flex: 1, gap: 2 },
  label: { ...typography.body, fontWeight: "700" },
  subtitle: { ...typography.bodySmall },
  divider: { height: StyleSheet.hairlineWidth },
  version: { ...typography.bodySmall, fontWeight: "600", textAlign: "center" },
  signOutRow: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: spacing.xs, minHeight: 44 },
  signOutText: { ...typography.body, fontWeight: "700" },
});
