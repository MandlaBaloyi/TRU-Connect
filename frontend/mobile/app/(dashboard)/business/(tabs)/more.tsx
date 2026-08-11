import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { LogOut, MoreVertical, User, Store, ShieldCheck, Settings as SettingsIcon } from "lucide-react-native";
import Constants from "expo-constants";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";
import { CardSection, Card } from "@/components/lists/CardListUI";
import { useLogout } from "@/features/auth/hooks/useAuth";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * More tab — moved onto the shared card system (see
 * src/components/lists/CardListUI.tsx), the same visual language as
 * Account Security and Settings, per direct feedback asking for the
 * same clean, elegant treatment here too.
 *
 * My Account, My Business, Account Security, and Settings each have
 * their own isolated feature folder + route (same separation as Order
 * Book/Loan Book) — all four navigate for real.
 */
const ROWS: { key: string; label: string; subtitle: string; route: string; icon: (color: string) => React.ReactNode }[] = [
  {
    key: "my-account",
    label: "My Account",
    subtitle: "Manage your personal information",
    route: "/business/my-account",
    icon: (c) => <User size={20} color={c} strokeWidth={2} />,
  },
  {
    key: "my-business",
    label: "My Business",
    subtitle: "Manage your business information",
    route: "/business/my-business",
    icon: (c) => <Store size={20} color={c} strokeWidth={2} />,
  },
  {
    key: "security",
    label: "Account Security",
    subtitle: "Protect your account and security",
    route: "/business/security",
    icon: (c) => <ShieldCheck size={20} color={c} strokeWidth={2} />,
  },
  {
    key: "settings",
    label: "Settings",
    subtitle: "Manage your app preferences",
    route: "/business/settings",
    icon: (c) => <SettingsIcon size={20} color={c} strokeWidth={2} />,
  },
];

export default function BusinessMore() {
  const router = useRouter();
  const theme = useTheme();
  const logout = useLogout();

  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      <AppHeader variant="title" title="More" rightIcon={<MoreVertical size={20} color={theme.colors.onSurface} />} />
      <View style={styles.content}>
        <CardSection>
          {ROWS.map((row) => (
            <Card
              key={row.key}
              icon={row.icon}
              label={row.label}
              description={row.subtitle}
              onPress={() => router.push(row.route as any)}
            />
          ))}
        </CardSection>

        <Text style={[styles.version, { color: theme.colors.onSurfaceVariant }]}>
          Version {Constants.expoConfig?.version ?? "1.0.0"}
        </Text>

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
  content: { gap: spacing.lg, paddingHorizontal: spacing.md, paddingTop: spacing.md, paddingBottom: spacing.lg },
  version: { ...typography.bodySmall, fontWeight: "600", textAlign: "center" },
  signOutRow: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: spacing.xs, minHeight: 44 },
  signOutText: { ...typography.body, fontWeight: "700" },
});
