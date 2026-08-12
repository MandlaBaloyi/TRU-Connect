import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import { useTheme } from "react-native-paper";
import { BadgeCheck } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { Hero, Note } from "@/components/lists/CardListUI";
import { useCurrentUser } from "@/features/auth/hooks/useCurrentUser";
import { spacing } from "@/theme/spacing";

import { VerificationBadge } from "../components/VerificationBadge";
import { toVerificationBadgeStatus } from "../types";

const EXPLAIN: Record<string, string> = {
  VERIFIED: "TruConnect has confirmed key details about this account. Verified accounts are generally more trusted by customers and suppliers.",
  PENDING: "Your verification is being reviewed. This can take a little while — you don't need to do anything else right now.",
  REQUIRED: "This account hasn't been verified yet. Verification helps customers and suppliers trust who they're dealing with.",
  FAILED: "Your last verification attempt wasn't successful. Contact support if you'd like to understand why, or if you'd like to try again.",
  UNAVAILABLE: "Verification status isn't available right now.",
};

/**
 * file.txt §18: explain what verification MEANS, no fake score, no
 * social-media blue-tick styling. Status itself is the REAL
 * AuthUser.verificationStatus — this screen never invents a value.
 */
export default function VerificationScreen() {
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

  const status = toVerificationBadgeStatus(user.verificationStatus);

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <Hero
          icon={<BadgeCheck size={28} color={theme.colors.primary} strokeWidth={1.8} />}
          title="Verification"
          description="A trust indicator, not a score — it tells people this account is genuinely who it says it is."
        />
        <View style={styles.badgeRow}>
          <VerificationBadge status={status} />
        </View>
        <Note>{EXPLAIN[status]}</Note>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.md },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  badgeRow: { alignItems: "center", marginVertical: spacing.sm },
});
