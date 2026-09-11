import React from "react";
import { ActivityIndicator, Alert, ScrollView, StyleSheet, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Sparkles } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { Hero, Note } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";

import { useSubscription } from "../hooks/useSubscription";
import { SUBSCRIPTION_TIERS } from "../services/subscriptionService";
import { SubscriptionTierCard } from "../components/SubscriptionTierCard";

/**
 * file.txt-adjacent: TruConnect's own platform-usage subscription,
 * not a stock-order/payment concept. Three tiers, everyone is FREE
 * right now (see types.ts's own note — genuinely hardcoded, no
 * billing infrastructure exists). Upgrade is real UI, honest outcome:
 * tapping it always surfaces a clear "not connected to billing yet"
 * message rather than silently succeeding or silently doing nothing.
 *
 * Enterprise is deliberately NOT listed — a later addition per the
 * product roadmap, not scoped yet; showing it here would imply a tier
 * that doesn't have real content behind it even as a placeholder.
 */
export default function SubscriptionScreen() {
  const theme = useTheme();
  const { subscription, isLoading, requestUpgrade, isUpgrading } = useSubscription();

  const handleUpgrade = (tierName: string) => {
    Alert.alert(tierName, "Upgrading isn't connected to real billing yet.", [
      {
        text: "OK",
        onPress: () => {
          requestUpgrade().catch(() => {
            // Error is expected and already shown via the Alert above
            // — this just prevents an unhandled rejection warning.
          });
        },
      },
    ]);
  };

  if (isLoading || !subscription) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Hero
          icon={<Sparkles size={28} color={theme.colors.primary} strokeWidth={1.8} />}
          title="Choose your plan"
          description="Higher plans unlock more orders, a larger catalogue, and priority placement in search."
        />

        {SUBSCRIPTION_TIERS.map((tier) => (
          <SubscriptionTierCard
            key={tier.tier}
            tier={tier}
            isCurrent={tier.tier === subscription.tier}
            onUpgrade={() => handleUpgrade(tier.name)}
            isUpgrading={isUpgrading}
          />
        ))}

        <Note>
          Exact limits and pricing for Pro and Max are still being finalised — what's shown here reflects the
          current plan, not a final commitment.
        </Note>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingHorizontal: spacing.md, paddingBottom: spacing.xxl, gap: spacing.md },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
});
