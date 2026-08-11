import React, { useState } from "react";
import { ScrollView, StyleSheet, Text } from "react-native";
import { useRouter } from "expo-router";
import { useTheme, TextInput } from "react-native-paper";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SecondaryButton } from "@/components/ui/SecondaryButton";
import { SecurityNote } from "../components/SecurityUI";
import { confirmTwoFactor } from "../services/securityService";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * Email 2FA enrolment.
 *
 * NO REAL EMAIL IS SENT — there is no backend endpoint for this yet,
 * and pretending to send one would be exactly the kind of fake
 * infrastructure this project has consistently refused. "Send code"
 * moves the UI to the entry step so the flow and layout are complete
 * and reviewable; wiring it is a one-line service change later.
 */
export default function TwoFactorEmailScreen() {
  const router = useRouter();
  const theme = useTheme();
  const [sent, setSent] = useState(false);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isWorking, setIsWorking] = useState(false);

  const handleVerify = async () => {
    setError(null);
    setIsWorking(true);
    try {
      await confirmTwoFactor("EMAIL", code);
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : "That code wasn't right. Try again.");
    } finally {
      setIsWorking(false);
    }
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
        <Text style={[styles.body, { color: theme.colors.onSurfaceVariant }]}>
          When you sign in, TruConnect will email you a 6-digit code. You'll enter it after your password.
        </Text>

        {!sent ? (
          <PrimaryButton onPress={() => setSent(true)}>Send me a code</PrimaryButton>
        ) : (
          <>
            <Text style={[styles.body, { color: theme.colors.onSurfaceVariant }]}>
              Enter the code we sent to the email address on your account.
            </Text>
            <TextInput
              mode="outlined"
              label="6-digit code"
              value={code}
              onChangeText={(t) => setCode(t.replace(/\D/g, "").slice(0, 6))}
              keyboardType="number-pad"
              maxLength={6}
            />
            {error && <Text style={[styles.error, { color: theme.colors.error }]}>{error}</Text>}

            <PrimaryButton onPress={handleVerify} loading={isWorking} disabled={code.length !== 6 || isWorking}>
              Turn on two-factor authentication
            </PrimaryButton>
            <SecondaryButton onPress={() => setSent(false)}>Send a new code</SecondaryButton>
          </>
        )}

        <SecurityNote>
          Keep the email address on your account up to date — it's how you'll receive your codes, and how you'd
          recover your account if you're ever locked out.
        </SecurityNote>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.md },
  body: { ...typography.body, lineHeight: 22 },
  error: { ...typography.bodySmall },
});
