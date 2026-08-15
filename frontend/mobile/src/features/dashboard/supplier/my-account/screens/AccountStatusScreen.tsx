import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { ShieldAlert } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { Card, CardSection, Hero, Note, StatusPill } from "@/components/lists/CardListUI";
import { useCurrentUser } from "@/features/auth/hooks/useCurrentUser";
import { spacing } from "@/theme/spacing";

/**
 * No "Contact support" row here, unlike business/my-account's own
 * AccountStatusScreen — that one links to Settings' real
 * report-problem screen, which doesn't exist on the supplier side yet
 * (Settings for supplier is explicitly a separate, later piece of
 * this build). The suspended-state Note below still tells the person
 * what to do; it just doesn't link anywhere that isn't real yet.
 */
export default function AccountStatusScreen() {
  const router = useRouter();
  const theme = useTheme();
  const { data: user, isLoading } = useCurrentUser();

  if (isLoading || !user) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  const status = user.accountStatus;

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <Hero
          icon={<ShieldAlert size={28} color={theme.colors.primary} strokeWidth={1.8} />}
          title="Account status"
          description="How TruConnect currently sees your account."
        />

        <View style={styles.pillRow}>
          <StatusPill
            label={status === "active" ? "Active" : status === "suspended" ? "Suspended" : status === "deactivated" ? "Deactivated" : "Unknown"}
            tone={status === "active" ? "on" : status === "suspended" ? "warning" : "off"}
          />
        </View>

        {status === "suspended" && (
          <Note>
            Your account has been suspended by TruConnect. Only TruConnect can lift a suspension — there's nothing
            to change here.
          </Note>
        )}

        {status === "deactivated" && (
          <Note>Your account is temporarily deactivated. Sign in again to reactivate it.</Note>
        )}

        {status === "active" && (
          <CardSection title="Manage">
            <Card label="Temporarily deactivate account" onPress={() => router.push("/supplier/my-account/deactivate-account" as any)} />
            <Card label="Delete account" onPress={() => router.push("/supplier/my-account/delete-account" as any)} />
          </CardSection>
        )}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.md },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  pillRow: { alignItems: "center" },
});
