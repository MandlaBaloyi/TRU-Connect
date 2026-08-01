import React, { useState } from "react";
import { StyleSheet } from "react-native";
import { Text } from "react-native-paper";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { FormTextField } from "@/components/forms/FormTextField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { forgotPasswordSchema, ForgotPasswordFormValues } from "@/features/auth/schemas/authSchemas";
import { useForgotPassword } from "@/features/auth/hooks/useAuth";
import { getErrorMessage } from "@/services/api/apiClient";
import { spacing } from "@/theme/spacing";

/**
 * Forgot Password screen.
 * Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt (Password Reset)
 *
 * Always shows the same SUCCESS message, whether or not the email
 * actually has an account -- matches the backend's enumeration-safe
 * /auth/forgot-password design. Never reveal account existence.
 *
 * The FAILURE message, by contrast, now uses getErrorMessage() rather
 * than a hardcoded string -- e.g. a rate-limit response from the
 * backend will show its own message instead of a generic one that
 * doesn't explain what actually happened.
 */
export default function ForgotPasswordScreen() {
  const router = useRouter();
  const forgotPassword = useForgotPassword();
  const [submitted, setSubmitted] = useState(false);

  const { control, handleSubmit } = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: "" },
  });

  const onSubmit = (values: ForgotPasswordFormValues) => {
    forgotPassword.mutate(values.email, { onSuccess: () => setSubmitted(true) });
  };

  if (submitted) {
    return (
      <ScreenContainer>
        <Text variant="headlineSmall" style={styles.title}>
          Check your email
        </Text>
        <Text style={styles.description}>
          If an account exists for that email address, we've sent instructions to reset your
          password.
        </Text>
        <PrimaryButton onPress={() => router.replace("/(auth)/sign-in")} style={{ marginTop: spacing.lg }}>
          Back to Sign In
        </PrimaryButton>
      </ScreenContainer>
    );
  }

  const errorMessage = forgotPassword.isError
    ? getErrorMessage(forgotPassword.error, "Check your connection and try again.")
    : null;

  return (
    <ScreenContainer>
      <Text variant="headlineSmall" style={styles.title}>
        Forgot your password?
      </Text>
      <Text style={styles.description}>
        Enter the email address on your account and we'll send you instructions to reset your
        password.
      </Text>

      <FormTextField
        control={control}
        name="email"
        label="Email Address"
        autoCapitalize="none"
        keyboardType="email-address"
      />

      {errorMessage && <Text style={styles.errorText}>{errorMessage}</Text>}

      <PrimaryButton
        onPress={handleSubmit(onSubmit)}
        loading={forgotPassword.isPending}
        style={{ marginTop: spacing.md }}
      >
        Send Reset Instructions
      </PrimaryButton>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontWeight: "700", marginTop: spacing.lg, marginBottom: spacing.sm },
  description: { opacity: 0.7, marginBottom: spacing.lg },
  errorText: { color: "#D64545", marginTop: spacing.sm },
});