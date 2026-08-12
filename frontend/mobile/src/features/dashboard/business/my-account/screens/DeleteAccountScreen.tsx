import React, { useState } from "react";
import { Alert, ScrollView, StyleSheet, Text, View } from "react-native";
import { TextInput, useTheme } from "react-native-paper";
import { AlertTriangle, Trash2 } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { Hero, Note } from "@/components/lists/CardListUI";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useDeletionRequest } from "../hooks/useAccountLifecycle";

/**
 * file.txt §4/§17: warning -> confirmation -> re-authentication ->
 * final confirmation, for a genuinely destructive action. Deletion is
 * NEVER performed here — see accountService.ts's docstring. The
 * password field is a mock re-auth gate only (accountService rejects
 * an empty password to exercise the failure path); a real
 * implementation verifies it server-side.
 */
type Step = "warning" | "reauth";

const CONSEQUENCES = [
  "Your Loan Book and Order Book records",
  "Your business profile",
  "Your payment method references",
  "Your verification status",
];

export default function DeleteAccountScreen() {
  const theme = useTheme();
  const { status, submit, isSubmitting, error } = useDeletionRequest();
  const [step, setStep] = useState<Step>("warning");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  if (status === "SUBMITTED") {
    return (
      <ScreenContainer hasNativeHeader>
        <ScrollView contentContainerStyle={styles.content}>
          <Hero
            icon={<Trash2 size={28} color={theme.colors.primary} strokeWidth={1.8} />}
            title="Deletion request recorded"
            description="Your account deletion request has been noted in this session."
          />
          <Note>
            This isn't connected to a live backend yet, so nothing has actually been deleted. When account deletion
            is fully built, submitting this request will genuinely start the deletion process.
          </Note>
        </ScrollView>
      </ScreenContainer>
    );
  }

  const confirmFinal = () => {
    Alert.alert(
      "Delete your account?",
      "This can't be undone once account deletion is fully built. This is your last chance to cancel.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete permanently",
          style: "destructive",
          onPress: async () => {
            setLocalError(null);
            try {
              await submit({ currentPassword: password });
            } catch (e) {
              setLocalError(e instanceof Error ? e.message : "Couldn't confirm your password. Try again.");
            }
          },
        },
      ]
    );
  };

  if (step === "reauth") {
    return (
      <ScreenContainer hasNativeHeader>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <Hero
            icon={<AlertTriangle size={28} color={theme.colors.error} strokeWidth={1.8} />}
            title="Confirm it's you"
            description="Enter your password to continue deleting your account."
          />
          <TextInput
            mode="outlined"
            label="Password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            autoCapitalize="none"
            autoFocus
          />
          {(localError || error) && (
            <Text style={[styles.error, { color: theme.colors.error }]}>
              {localError ?? (error instanceof Error ? error.message : "")}
            </Text>
          )}
          <PrimaryButton
            onPress={confirmFinal}
            loading={isSubmitting}
            disabled={password.length === 0 || isSubmitting}
            buttonColor={theme.colors.error}
          >
            Continue
          </PrimaryButton>
        </ScrollView>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <Hero
          icon={<Trash2 size={28} color={theme.colors.error} strokeWidth={1.8} />}
          title="Delete account"
          description="Permanently request deletion of your TruConnect account."
        />

        <View style={[styles.warningCard, { backgroundColor: theme.colors.errorContainer }]}>
          <Text style={[styles.warningTitle, { color: theme.colors.error }]}>This will eventually remove:</Text>
          {CONSEQUENCES.map((item) => (
            <Text key={item} style={[styles.warningItem, { color: theme.colors.error }]}>
              •  {item}
            </Text>
          ))}
        </View>

        <Note>
          Once account deletion is fully built, this action won't be reversible. You'll be asked to confirm your
          password before it's submitted.
        </Note>

        <PrimaryButton onPress={() => setStep("reauth")} buttonColor={theme.colors.error}>
          Continue to delete my account
        </PrimaryButton>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.md },
  warningCard: { borderRadius: radius.lg, padding: spacing.md, gap: spacing.xs },
  warningTitle: { ...typography.body, fontWeight: "700" },
  warningItem: { ...typography.bodySmall },
  error: { ...typography.bodySmall },
});
