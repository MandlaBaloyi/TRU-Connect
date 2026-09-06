import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { CreditCard, Receipt, ShieldAlert, Sparkles, Trash2, UserX } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { Card, CardSection, StatusPill } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useAccountProfile } from "../hooks/useAccountProfile";
import { usePaymentMethods } from "../hooks/usePaymentMethods";
import { useSubscription } from "../hooks/useSubscription";
import { ProfileHeader } from "../components/ProfileHeader";

/**
 * Supplier My Account landing screen. Direct counterpart to
 * business/my-account/screens/MyAccountScreen.tsx.
 *
 * REVISED, same reorganisation as the business side: Contact details
 * and About no longer have their own sections here — both moved into
 * the consolidated Profile screen, reached via the header's pencil
 * icon. This screen keeps the read-only preview plus Payment methods
 * (the receiving side — see types.ts's own note), Subscription,
 * Billing, Account status, and Danger zone.
 *
 * Photo upload is now real (see ProfileScreen.tsx's own note) — the
 * avatar here now matches business's exact behaviour: tappable
 * (opens Profile), no camera badge (that control lives on Profile
 * now, avoiding the duplicate-control problem the business side
 * already fixed the same way).
 */
export default function SupplierMyAccountScreen() {
  const router = useRouter();
  const theme = useTheme();

  const { summary, isLoading, isError, refetch } = useAccountProfile();
  const { paymentMethods } = usePaymentMethods();
  const { subscription } = useSubscription();

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !summary) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load your account. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const go = (path: string) => () => router.push(path as any);

  const fullName = [summary.firstName, summary.lastName].filter(Boolean).join(" ") || summary.email;
  const displayName = summary.businessName?.trim() || fullName;
  const openProfile = go("/supplier/my-account/profile");
  const accountStatusTone =
    summary.accountStatus === "active" ? "on" : summary.accountStatus === "suspended" ? "warning" : "off";
  const accountStatusLabel =
    summary.accountStatus === "active"
      ? "Active"
      : summary.accountStatus === "suspended"
        ? "Suspended"
        : summary.accountStatus === "deactivated"
          ? "Deactivated"
          : "Unknown";

  return (
    <ScreenContainer hasNativeHeader paddingHorizontal={0}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <ProfileHeader
          displayName={displayName}
          secondaryName={fullName}
          coverUri={summary.coverImageUrl}
          avatarUri={summary.businessImageUrl}
          verified={summary.verification === "VERIFIED"}
          bio={summary.bio}
          onCoverPress={openProfile}
          onAvatarPress={openProfile}
        />

        <View style={styles.body}>
          {/* Payment methods — the RECEIVING side, see types.ts's own note */}
          <CardSection title="Payment methods">
            <Card
              icon={(c) => <CreditCard size={20} color={c} />}
              label="How you get paid"
              description={
                paymentMethods.find((m) => m.isDefault)?.displayLabel
                  ? `Default: ${paymentMethods.find((m) => m.isDefault)?.displayLabel}`
                  : `${paymentMethods.length} method(s)`
              }
              onPress={go("/supplier/my-account/payment-methods")}
            />
          </CardSection>

          {/* Subscription & Billing */}
          <CardSection title="Subscription">
            <Card
              icon={(c) => <Sparkles size={20} color={c} />}
              label="Plan"
              description={subscription ? `You're on ${subscription.tier === "FREE" ? "the Free plan" : subscription.tier}` : "Loading…"}
              onPress={go("/supplier/my-account/subscription")}
            />
            <Card
              icon={(c) => <Receipt size={20} color={c} />}
              label="Billing"
              description="Your plan and TruConnect's billing cycle"
              onPress={go("/supplier/my-account/billing")}
            />
          </CardSection>

          {/* Account status */}
          <CardSection title="Account status">
            <Card
              label="Status"
              description="How TruConnect sees your account right now"
              status={<StatusPill label={accountStatusLabel} tone={accountStatusTone} />}
              onPress={go("/supplier/my-account/account-status")}
            />
          </CardSection>

          {/* Danger zone — visually separated */}
          <CardSection title="Danger zone">
            <Card
              tone="danger"
              icon={(c) => <UserX size={20} color={c} />}
              label="Temporarily deactivate account"
              description="Hide your account until you come back"
              onPress={go("/supplier/my-account/deactivate-account")}
            />
            <Card
              tone="danger"
              icon={(c) => <Trash2 size={20} color={c} />}
              label="Delete account"
              description="Permanently request account deletion"
              onPress={go("/supplier/my-account/delete-account")}
            />
          </CardSection>

          {summary.accountStatus === "suspended" && (
            <View style={[styles.suspendedNote, { backgroundColor: theme.colors.errorContainer }]}>
              <ShieldAlert size={18} color={theme.colors.error} />
              <Text style={[styles.suspendedText, { color: theme.colors.error }]}>
                Your account is suspended by TruConnect. Only TruConnect can lift a suspension.
              </Text>
            </View>
          )}
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingBottom: spacing.xxl },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  body: { paddingHorizontal: spacing.md, paddingTop: spacing.lg, gap: spacing.xl },
  suspendedNote: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    padding: spacing.md,
    borderRadius: 12,
  },
  suspendedText: { ...typography.bodySmall, flex: 1, lineHeight: 18 },
});
