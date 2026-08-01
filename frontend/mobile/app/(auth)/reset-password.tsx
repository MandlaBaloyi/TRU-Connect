import React, { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter, useLocalSearchParams } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PasswordField } from "@/components/forms/PasswordField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { EmptyState } from "@/components/feedback/EmptyState";
import { resetPasswordSchema, ResetPasswordFormValues } from "@/features/auth/schemas/authSchemas";
import { useResetPassword, useValidateResetTicket } from "@/features/auth/hooks/useAuth";
import { getErrorMessage } from "@/services/api/apiClient";
import { spacing } from "@/theme/spacing";

/**
 * Reset Password screen.
 * Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt (Password Reset); Auth
 * Hardening master prompt, Objectives 6 and 7.
 *
 * Reached via the reset email's link:
 *   {APP_BASE_URL}/reset-password?ticket=...
 * which bounces (via src/domains/platform/api/reset_redirect_routes.py)
 * into this screen's deep link: truconnect://reset-password?ticket=...
 *
 * On mount, the ticket is validated immediately (GET /auth/reset-password
 * /validate) so an expired or already-used link shows a clear message
 * right away -- rather than only failing after the user has typed a new
 * password and pressed submit (Objective 6: "Backend returns ticket
 * validation status. Frontend simply renders UI.").
 */
export default function ResetPasswordScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { ticket } = useLocalSearchParams<{ ticket?: string }>();

  const validateTicket = useValidateResetTicket();
  const resetPassword = useResetPassword();
  const [done, setDone] = useState(false);

  const { control, handleSubmit } = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { newPassword: "", confirmPassword: "" },
  });

  useEffect(() => {
    if (ticket) {
      validateTicket.mutate(ticket);
    }
    // Only run once per ticket value -- validateTicket itself is stable
    // across renders (React Query mutation), so it's intentionally left
    // out of the dependency array to avoid re-validating on every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticket]);

  if (!ticket) {
    return (
      <ScreenContainer>
        <EmptyState message="This password reset link is invalid. Request a new one from the Sign In screen." />
      </ScreenContainer>
    );
  }

  if (validateTicket.isPending || validateTicket.isIdle) {
    return (
      <ScreenContainer>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (validateTicket.isError || validateTicket.data === false) {
    return (
      <ScreenContainer>
        <EmptyState message="This password reset link has expired or was already used. Request a new one from the Sign In screen." />
        <PrimaryButton onPress={() => router.replace("/(auth)/forgot-password")} style={{ marginTop: spacing.lg }}>
          Request New Link
        </PrimaryButton>
      </ScreenContainer>
    );
  }

  if (done) {
    return (
      <ScreenContainer>
        <Text variant="headlineSmall" style={styles.title}>
          Password updated
        </Text>
        <Text style={styles.description}>
          Your password has been changed. Please sign in with your new password.
        </Text>
        <PrimaryButton onPress={() => router.replace("/(auth)/sign-in")} style={{ marginTop: spacing.lg }}>
          Go to Sign In
        </PrimaryButton>
      </ScreenContainer>
    );
  }

  const onSubmit = (values: ResetPasswordFormValues) => {
    resetPassword.mutate(
      { ticket, newPassword: values.newPassword, confirmPassword: values.confirmPassword },
      { onSuccess: () => setDone(true) }
    );
  };

  const errorMessage = resetPassword.isError
    ? getErrorMessage(resetPassword.error, "This reset link is invalid or has expired. Request a new one.")
    : null;

  return (
    <ScreenContainer>
      <Text variant="headlineSmall" style={styles.title}>
        Set a new password
      </Text>

      <PasswordField control={control} name="newPassword" label="New Password" />
      <PasswordField control={control} name="confirmPassword" label="Confirm New Password" />

      {errorMessage && <Text style={styles.errorText}>{errorMessage}</Text>}

      <PrimaryButton
        onPress={handleSubmit(onSubmit)}
        loading={resetPassword.isPending}
        style={{ marginTop: spacing.md }}
      >
        Reset Password
      </PrimaryButton>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  title: { fontWeight: "700", marginTop: spacing.lg, marginBottom: spacing.sm },
  description: { opacity: 0.7, marginBottom: spacing.lg },
  errorText: { color: "#D64545", marginTop: spacing.sm },
});