import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Receipt } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { Card, CardSection, Hero, Note } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useSubscription } from "../hooks/useSubscription";
import { SUBSCRIPTION_TIERS } from "../services/subscriptionService";

/**
 * TruConnect's own billing cycle for the account's subscription —
 * informational only, no real invoices or charge history exist
 * because no billing infrastructure exists (see types.ts's own note).
 * On Free, there's genuinely nothing to bill — said plainly rather
 * than showing an empty "billing history" section that implies
 * charges are expected but just haven't happened yet.
 */
export default function BillingScreen() {
  const router = useRouter();
  const theme = useTheme();
  const { subscription, isLoading } = useSubscription();

  if (isLoading || !subscription) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  const currentTierInfo = SUBSCRIPTION_TIERS.find((t) => t.tier === subscription.tier);

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <Hero
          icon={<Receipt size={28} color={theme.colors.primary} strokeWidth={1.8} />}
          title="Billing"
          description="Your current plan and TruConnect's billing cycle."
        />

        <CardSection title="Current plan">
          <Card
            label={currentTierInfo?.name ?? "Supplier Free"}
            description={
              subscription.nextBillingDate
                ? `Next billing date: ${subscription.nextBillingDate}`
                : "You're on the Free plan — there's nothing to bill."
            }
            onPress={() => router.push("/supplier/my-account/subscription" as any)}
          />
        </CardSection>

        {subscription.tier === "FREE" ? (
          <Note>Upgrade to Pro or Max to unlock more orders, a larger catalogue, and priority placement.</Note>
        ) : (
          <>
            <Text style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>Billing history</Text>
            <Text style={[styles.emptyText, { color: theme.colors.onSurfaceVariant }]}>
              No billing history yet — this will show past charges once real billing is connected.
            </Text>
          </>
        )}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingHorizontal: spacing.md, paddingBottom: spacing.xxl, gap: spacing.md },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  sectionTitle: { ...typography.h2, marginTop: spacing.sm },
  emptyText: { ...typography.bodySmall, lineHeight: 19 },
});
