import React from "react";
import { StyleSheet, View } from "react-native";
import { Text, Divider } from "react-native-paper";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { FormTextField } from "@/components/forms/FormTextField";
import { PasswordField } from "@/components/forms/PasswordField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SecondaryButton } from "@/components/ui/SecondaryButton";
import { signInSchema, SignInFormValues } from "@/features/auth/schemas/authSchemas";
import { useSignIn } from "@/features/auth/hooks/useAuth";
import { ApiError } from "@/services/api/apiClient";
import { spacing } from "@/theme/spacing";

/**
 * Sign In screen.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 4)
 *
 * "Remember Me" REMOVED: it was wired to nothing. Tokens are always
 * persisted to SecureStore (the app can't function without them), so the
 * checkbox previously had zero effect regardless of its state -- a UI
 * element that lies about doing something is worse than not having it.
 * A real "sign out on app close" mode is a genuine feature (needs
 * app-lifecycle handling to clear the refresh token on background/quit)
 * and is worth building deliberately if you want it, not as a decorative
 * checkbox.
 */
export default function SignInScreen() {
  const signIn = useSignIn();

  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<SignInFormValues>({
    resolver: zodResolver(signInSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = (values: SignInFormValues) => {
    signIn.mutate({ email: values.email, password: values.password });
  };

  const errorMessage =
    signIn.error instanceof ApiError
      ? signIn.error.message
      : signIn.isError
      ? "We couldn't sign you in. Please check your details and try again."
      : null;

  return (
    <ScreenContainer>
      <Text variant="headlineSmall" style={styles.title}>
        Welcome back
      </Text>

      <FormTextField
        control={control}
        name="email"
        label="Email Address"
        autoCapitalize="none"
        keyboardType="email-address"
      />
      <PasswordField control={control} name="password" label="Password" />

      <View style={styles.forgotRow}>
        <Link href="/(auth)/forgot-password">
          <Text style={styles.link}>Forgot Password?</Text>
        </Link>
      </View>

      {errorMessage && <Text style={styles.errorText}>{errorMessage}</Text>}

      <PrimaryButton
        onPress={handleSubmit(onSubmit)}
        loading={isSubmitting || signIn.isPending}
        style={{ marginTop: spacing.md }}
      >
        Sign In
      </PrimaryButton>

      <Divider style={{ marginVertical: spacing.lg }} />
      <Text style={styles.orText}>OR</Text>

      <SecondaryButton icon="google" onPress={() => {}} style={{ marginTop: spacing.md }}>
        Continue with Google
      </SecondaryButton>

      <View style={styles.footerRow}>
        <Text>Don't have an account? </Text>
        <Link href="/(onboarding)/role-selection">
          <Text style={styles.link}>Create Account</Text>
        </Link>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontWeight: "700", marginTop: spacing.lg, marginBottom: spacing.lg },
  forgotRow: { alignItems: "flex-end", marginBottom: spacing.md },
  link: { fontWeight: "600" },
  orText: { textAlign: "center", opacity: 0.6, marginTop: -spacing.lg },
  errorText: { color: "#D64545", marginBottom: spacing.sm },
  footerRow: { flexDirection: "row", justifyContent: "center", marginTop: spacing.lg },
});