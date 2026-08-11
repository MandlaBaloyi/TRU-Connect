import React, { useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Switch, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Fingerprint } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { SecurityHero, SecurityNote } from "../components/SecurityUI";
import { useBiometrics } from "../hooks/useBiometrics";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * Biometric sign-in.
 *
 * FINGERPRINT AND FACIAL RECOGNITION NAMED TOGETHER — per direct
 * instruction, the copy explicitly says "Fingerprint or Facial
 * Recognition" rather than fingerprint alone. Underneath, the OS still
 * authenticates with whatever the device actually offers (fingerprint,
 * face, or both) — useBiometrics simply calls
 * LocalAuthentication.authenticateAsync() and lets the OS decide which
 * method to prompt for, so a phone with only face unlock still works
 * correctly. This is a wording choice, not a functionality change.
 *
 * Three distinct device states still get three distinct screens (no
 * hardware / hardware not enrolled / ready), because each genuinely
 * needs a different message and action — that structure is unchanged.
 */
export default function BiometricsScreen() {
  const theme = useTheme();
  const { isAvailable, isEnrolled, isEnabledForApp, isLoading, setEnabled } = useBiometrics();
  const [isToggling, setIsToggling] = useState(false);

  const handleToggle = async (next: boolean) => {
    setIsToggling(true);
    try {
      await setEnabled(next);
    } finally {
      setIsToggling(false);
    }
  };

  if (isLoading) {
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
        {!isAvailable ? (
          <>
            <SecurityHero
              icon={<Fingerprint size={28} color={theme.colors.onSurfaceVariant} strokeWidth={1.8} />}
              title="Not available on this device"
              description="This phone doesn't have a fingerprint reader, so biometric sign-in can't be used here. Your password and two-factor authentication still protect your account."
            />
          </>
        ) : !isEnrolled ? (
          <>
            <SecurityHero
              icon={<Fingerprint size={28} color={theme.colors.primary} strokeWidth={1.8} />}
              title="Set up your fingerprint first"
              description="Your phone supports fingerprint sign-in, but you haven't set one up yet. Add it in your phone's own security settings, then come back here to turn it on for TruConnect."
            />
          </>
        ) : (
          <>
            <SecurityHero
              icon={<Fingerprint size={28} color={theme.colors.primary} strokeWidth={1.8} />}
              title="Sign in with your Fingerprint or Facial Recognition"
              description="Open TruConnect with your fingerprint or facial recognition instead of typing your password every time."
            />

            <View style={[styles.toggleRow, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
              <Text style={[styles.toggleLabel, { color: theme.colors.onSurface }]}>
                Use your Fingerprint or Facial Recognition
              </Text>
              <Switch
                value={isEnabledForApp}
                onValueChange={handleToggle}
                disabled={isToggling}
                accessibilityLabel="Use your Fingerprint or Facial Recognition"
              />
            </View>

            <SecurityNote>
              Your fingerprint or facial recognition never leaves your phone — TruConnect only ever asks your phone
              whether it's you, and gets a yes or no back. You can always sign in with your password instead.
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
  toggleRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.md,
    padding: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
  },
  toggleLabel: { ...typography.body, fontWeight: "700", flexShrink: 1 },
});
