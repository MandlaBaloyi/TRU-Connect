import React from "react";
import { StyleSheet, View } from "react-native";
import { Text, Checkbox, Divider } from "react-native-paper";
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
import { spacing } from "@/theme/spacing";

/**
 * Sign In screen.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 4) and
 * docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.1 (POST /auth/login).
 */
export default function SignInScreen() {
  const signIn = useSignIn();

  const {
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { isSubmitting },
  } = useForm<SignInFormValues>({
    resolver: zodResolver(signInSchema),
    defaultValues: { email: "", password: "", rememberMe: false },
  });

  const rememberMe = watch("rememberMe");

  const onSubmit = (values: SignInFormValues) => {
    signIn.mutate({ email: values.email, password: values.password });
  };

  return (
    <ScreenContainer>
      <Text variant="headlineSmall" style={styles.title}>
        Welcome Back
      </Text>

      <FormTextField control={control} name="email" label="Email Address" autoCapitalize="none" keyboardType="email-address" />
      <PasswordField control={control} name="password" label="Password" />

      <View style={styles.row}>
        <Checkbox
          status={rememberMe ? "checked" : "unchecked"}
          onPress={() => setValue("rememberMe", !rememberMe)}
        />
        <Text onPress={() => setValue("rememberMe", !rememberMe)}>Remember Me</Text>
        <View style={{ flex: 1 }} />
        <Text style={styles.link}>Forgot Password?</Text>
      </View>

      {signIn.isError && (
        <Text style={styles.errorText}>
          We couldn't sign you in. Please check your details and try again.
        </Text>
      )}

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
  row: { flexDirection: "row", alignItems: "center", marginBottom: spacing.md },
  link: { fontWeight: "600" },
  orText: { textAlign: "center", opacity: 0.6, marginTop: -spacing.lg },
  errorText: { color: "#D64545", marginBottom: spacing.sm },
  footerRow: { flexDirection: "row", justifyContent: "center", marginTop: spacing.lg },
});
