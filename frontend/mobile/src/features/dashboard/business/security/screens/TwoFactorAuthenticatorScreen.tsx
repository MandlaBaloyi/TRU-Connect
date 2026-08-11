import React, { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme, TextInput } from "react-native-paper";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SecurityNote } from "../components/SecurityUI";
import { startAuthenticatorEnrolment, confirmTwoFactor } from "../services/securityService";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * Authenticator app enrolment.
 *
 * THE SECRET IS HELD IN COMPONENT STATE ONLY — never persisted, never
 * logged, and discarded when this screen unmounts (spec §18.7).
 *
 * NO QR CODE IS RENDERED YET, deliberately: this project has no QR
 * library installed, and adding one is a dependency decision rather
 * than something to slip in silently. The manual-entry key below is a
 * genuine, complete enrolment path that every authenticator app
 * supports — so the flow is fully usable today, and a QR image can be
 * added later purely as a convenience without changing this flow.
 */
export default function TwoFactorAuthenticatorScreen() {
  const router = useRouter();
  const theme = useTheme();
  const [secret, setSecret] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);

  useEffect(() => {
    let cancelled = false;
    startAuthenticatorEnrolment().then((enrolment) => {
      if (!cancelled) setSecret(enrolment.secret);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleVerify = async () => {
    setError(null);
    setIsVerifying(true);
    try {
      await confirmTwoFactor("AUTHENTICATOR", code);
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : "That code wasn't right. Try again.");
    } finally {
      setIsVerifying(false);
    }
  };

  if (!secret) {
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
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
        <Text style={[styles.step, { color: theme.colors.onSurface }]}>1. Install an authenticator app</Text>
        <Text style={[styles.body, { color: theme.colors.onSurfaceVariant }]}>
          Google Authenticator, Microsoft Authenticator and Authy all work. Any of them is fine.
        </Text>

        <Text style={[styles.step, { color: theme.colors.onSurface }]}>2. Add this key to the app</Text>
        <View style={[styles.secretBox, { backgroundColor: theme.colors.surfaceVariant }]}>
          <Text style={[styles.secret, { color: theme.colors.onSurface }]} selectable>
            {secret}
          </Text>
        </View>
        <Text style={[styles.body, { color: theme.colors.onSurfaceVariant }]}>
          Choose "enter a setup key" in your authenticator app, then type this in. Name it TruConnect so you recognise
          it later.
        </Text>

        <Text style={[styles.step, { color: theme.colors.onSurface }]}>3. Enter the 6-digit code it shows</Text>
        <TextInput
          mode="outlined"
          label="6-digit code"
          value={code}
          onChangeText={(t) => setCode(t.replace(/\D/g, "").slice(0, 6))}
          keyboardType="number-pad"
          maxLength={6}
        />
        {error && <Text style={[styles.error, { color: theme.colors.error }]}>{error}</Text>}

        <PrimaryButton onPress={handleVerify} loading={isVerifying} disabled={code.length !== 6 || isVerifying}>
          Turn on two-factor authentication
        </PrimaryButton>

        <SecurityNote>
          Keep this key private. Anyone who has it can generate your codes. If you lose access to your authenticator
          app, you can still sign in using your email.
        </SecurityNote>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.sm },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  step: { ...typography.body, fontWeight: "700", marginTop: spacing.sm },
  body: { ...typography.bodySmall, lineHeight: 19 },
  secretBox: { padding: spacing.md, borderRadius: radius.md, alignItems: "center", marginVertical: spacing.xs },
  secret: { ...typography.h2, letterSpacing: 2 },
  error: { ...typography.bodySmall },
});
