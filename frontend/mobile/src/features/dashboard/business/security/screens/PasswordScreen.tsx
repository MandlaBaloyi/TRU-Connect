import React, { useCallback, useState } from "react";
import { ScrollView, StyleSheet } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { useTheme } from "react-native-paper";
import { KeyRound, RotateCcw, Lock } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { SecurityHero, SecuritySection, SecurityCard, SecurityNote, formatWhen } from "../components/SecurityUI";
import { getSecurityOverview } from "../services/securityService";
import { spacing } from "@/theme/spacing";

/** Password overview — redesigned around a clear hero explanation and
 *  card-based actions, replacing the earlier plain-text status line. */
export default function PasswordScreen() {
  const router = useRouter();
  const theme = useTheme();
  const [lastChangedAt, setLastChangedAt] = useState<string | null | undefined>(undefined);

  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      getSecurityOverview().then((o) => {
        if (!cancelled) setLastChangedAt(o.password.lastChangedAt);
      });
      return () => {
        cancelled = true;
      };
    }, [])
  );

  const description =
    lastChangedAt === undefined
      ? "Checking your password status…"
      : lastChangedAt
        ? `Last changed ${formatWhen(lastChangedAt)}. A strong, unique password is your first line of defence.`
        : "You haven't changed your password since creating your account. A strong, unique password is your first line of defence.";

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <SecurityHero
          icon={<Lock size={28} color={theme.colors.primary} strokeWidth={1.8} />}
          title="Password"
          description={description}
        />

        <SecuritySection>
          <SecurityCard
            icon={(c) => <KeyRound size={20} color={c} />}
            label="Change password"
            description="You'll need your current password"
            onPress={() => router.push("/business/security/change-password" as any)}
          />
          <SecurityCard
            icon={(c) => <RotateCcw size={20} color={c} />}
            label="Forgot your password?"
            description="Reset it using your email"
            onPress={() => router.push("/(auth)/forgot-password" as any)}
          />
        </SecuritySection>

        <SecurityNote>
          A strong password is at least 8 characters and mixes letters, numbers and symbols. Don't reuse a password
          from another app — if that app is ever breached, your business records shouldn't be at risk too.
        </SecurityNote>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.lg },
});
