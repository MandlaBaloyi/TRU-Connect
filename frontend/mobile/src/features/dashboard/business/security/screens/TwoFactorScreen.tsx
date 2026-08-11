import React, { useCallback, useState } from "react";
import { ActivityIndicator, Alert, ScrollView, StyleSheet, View } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { useTheme } from "react-native-paper";
import { Smartphone, Mail, ShieldCheck } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { SecondaryButton } from "@/components/ui/SecondaryButton";
import { SecurityHero, SecuritySection, SecurityCard, SecurityNote, StatusPill, formatWhen } from "../components/SecurityUI";
import { getTwoFactorStatus, disableTwoFactor } from "../services/securityService";
import type { TwoFactorStatus } from "../types";
import { spacing } from "@/theme/spacing";

/**
 * 2FA method selection + management — redesigned to a hero + card
 * layout. Both methods are presented as legitimate: the authenticator
 * app is marked "Recommended" because it genuinely is stronger, but
 * email verification is described by its real advantage (nothing
 * extra to install) rather than framed as unsafe.
 */
export default function TwoFactorScreen() {
  const router = useRouter();
  const theme = useTheme();
  const [status, setStatus] = useState<TwoFactorStatus | null>(null);
  const [isWorking, setIsWorking] = useState(false);

  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      getTwoFactorStatus().then((s) => {
        if (!cancelled) setStatus(s);
      });
      return () => {
        cancelled = true;
      };
    }, [])
  );

  if (!status) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  const confirmDisable = () => {
    Alert.alert(
      "Turn off two-factor authentication?",
      "Your account will be protected by your password alone. This makes it easier for someone else to sign in as you.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Turn off",
          style: "destructive",
          onPress: async () => {
            setIsWorking(true);
            try {
              await disableTwoFactor();
              setStatus(await getTwoFactorStatus());
            } finally {
              setIsWorking(false);
            }
          },
        },
      ]
    );
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <SecurityHero
          icon={<ShieldCheck size={28} color={theme.colors.primary} strokeWidth={1.8} />}
          title="Two-factor authentication"
          description="Adds a second step to signing in — so even if someone learns your password, they still can't get into your account."
        />

        {status.isEnabled ? (
          <>
            <SecuritySection title="Current method">
              <SecurityCard
                icon={(c) =>
                  status.activeMethod === "AUTHENTICATOR" ? <Smartphone size={20} color={c} /> : <Mail size={20} color={c} />
                }
                label={status.activeMethod === "AUTHENTICATOR" ? "Authenticator app" : "Email verification"}
                description={status.enabledAt ? `Turned on ${formatWhen(status.enabledAt)}` : undefined}
                status={<StatusPill label="On" tone="on" />}
                onPress={() =>
                  router.push(
                    (status.activeMethod === "AUTHENTICATOR"
                      ? "/business/security/two-factor-authenticator"
                      : "/business/security/two-factor-email") as any
                  )
                }
              />
            </SecuritySection>

            <SecondaryButton onPress={confirmDisable} loading={isWorking} disabled={isWorking}>
              Turn off two-factor authentication
            </SecondaryButton>
          </>
        ) : (
          <>
            <SecuritySection title="Choose a method">
              <SecurityCard
                icon={(c) => <Smartphone size={20} color={c} />}
                label="Authenticator app"
                description="Codes from an app on your phone. Works without signal."
                status={<StatusPill label="Recommended" tone="on" />}
                onPress={() => router.push("/business/security/two-factor-authenticator" as any)}
              />
              <SecurityCard
                icon={(c) => <Mail size={20} color={c} />}
                label="Email verification"
                description="A code sent to your email. Nothing extra to install."
                onPress={() => router.push("/business/security/two-factor-email" as any)}
              />
            </SecuritySection>

            <SecurityNote>
              Both methods genuinely protect your account. An authenticator app is stronger because the codes never
              travel anywhere — but if email is easier for you to manage day to day, that's a good choice too.
            </SecurityNote>
          </>
        )}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.lg },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
});
