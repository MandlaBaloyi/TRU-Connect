import React, { useEffect, useState } from "react";
import { StyleSheet, View, ScrollView } from "react-native";
import { Text, Checkbox, Divider } from "react-native-paper";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { FormTextField } from "@/components/forms/FormTextField";
import { PasswordField } from "@/components/forms/PasswordField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SecondaryButton } from "@/components/ui/SecondaryButton";
import {
  businessRegisterSchema,
  BusinessRegisterFormValues,
  supplierRegisterSchema,
  SupplierRegisterFormValues,
} from "@/features/auth/schemas/authSchemas";
import { useRegister, useGoogleSignIn } from "@/features/auth/hooks/useAuth";
import { secureStorage } from "@/services/storage/secureStorage";
import { STORAGE_KEYS } from "@/constants/config";
import { ApiError, getErrorMessage } from "@/services/api/apiClient";
import type { UserRole } from "@/features/auth/types";
import { spacing } from "@/theme/spacing";

/**
 * Create Account screen.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 5)
 *
 * Three fixes here that were previously silent:
 *  1. register.isError was never read -- a duplicate-email 409 produced
 *     no feedback at all; the user just saw nothing happen.
 *  2. The Privacy Policy / Terms checkbox is validated by the Zod schema
 *     (z.literal(true)) but was never wrapped in anything that displays
 *     formState.errors -- so an unchecked box silently blocked
 *     submission with zero visible reason why.
 *  3. registerErrorMessage only recognized ApiError instances -- when
 *     authService.register() crashed with a plain TypeError (reading
 *     .tokens off a response that no longer has one, pre-hardening-fix),
 *     that check was too narrow to catch it, so the screen showed
 *     nothing even though the mutation had failed. getErrorMessage()
 *     always returns something displayable, for any error shape.
 */
export default function CreateAccountScreen() {
  const register = useRegister();
  const googleSignIn = useGoogleSignIn();
  const [role, setRole] = useState<UserRole>("business");

  useEffect(() => {
    secureStorage.getItem(STORAGE_KEYS.SELECTED_ROLE).then((stored) => {
      if (stored === "supplier" || stored === "business") setRole(stored);
    });
  }, []);

  const registerErrorMessage = register.isError
    ? getErrorMessage(register.error, "We couldn't create your account. Please try again.")
    : null;
  const isDuplicateEmail = register.error instanceof ApiError && register.error.status === 409;

  return role === "business" ? (
    <BusinessRegisterForm
      onSubmit={(values) => register.mutate({ role: "business", ...values })}
      isSubmitting={register.isPending}
      errorMessage={registerErrorMessage}
      isDuplicateEmail={isDuplicateEmail}
      onGooglePress={() => googleSignIn.mutate("")}
      isGoogleLoading={googleSignIn.isPending}
    />
  ) : (
    <SupplierRegisterForm
      onSubmit={(values) => register.mutate({ role: "supplier", ...values })}
      isSubmitting={register.isPending}
      errorMessage={registerErrorMessage}
      isDuplicateEmail={isDuplicateEmail}
      onGooglePress={() => googleSignIn.mutate("")}
      isGoogleLoading={googleSignIn.isPending}
    />
  );
}

interface CommonProps {
  onGooglePress: () => void;
  isGoogleLoading: boolean;
  errorMessage: string | null;
  isDuplicateEmail: boolean;
}

function RegisterError({ errorMessage, isDuplicateEmail }: Pick<CommonProps, "errorMessage" | "isDuplicateEmail">) {
  if (!errorMessage) return null;
  return (
    <View style={{ marginBottom: spacing.md }}>
      <Text style={styles.errorText}>{errorMessage}</Text>
      {isDuplicateEmail && (
        <Link href="/(auth)/sign-in">
          <Text style={styles.link}>Sign in instead</Text>
        </Link>
      )}
    </View>
  );
}

function BusinessRegisterForm({
  onSubmit,
  isSubmitting,
  errorMessage,
  isDuplicateEmail,
  onGooglePress,
  isGoogleLoading,
}: {
  onSubmit: (values: BusinessRegisterFormValues) => void;
  isSubmitting: boolean;
} & CommonProps) {
  const {
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<BusinessRegisterFormValues>({
    resolver: zodResolver(businessRegisterSchema),
    defaultValues: {
      firstName: "",
      lastName: "",
      businessName: "",
      email: "",
      password: "",
      confirmPassword: "",
      acceptPrivacyPolicy: undefined as unknown as true,
    },
  });
  const accepted = watch("acceptPrivacyPolicy");

  return (
    <ScreenContainer>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        <Text variant="headlineSmall" style={styles.title}>
          Create Your Business Account
        </Text>

        <RegisterError errorMessage={errorMessage} isDuplicateEmail={isDuplicateEmail} />

        <FormTextField control={control} name="firstName" label="First Name" />
        <FormTextField control={control} name="lastName" label="Last Name" />
        <FormTextField control={control} name="businessName" label="Business Name (optional)" />
        <FormTextField control={control} name="email" label="Email Address" autoCapitalize="none" keyboardType="email-address" />
        <PasswordField control={control} name="password" label="Password" />
        <PasswordField control={control} name="confirmPassword" label="Confirm Password" />

        <View style={styles.row}>
          <Checkbox
            status={accepted ? "checked" : "unchecked"}
            onPress={() => setValue("acceptPrivacyPolicy", !accepted as unknown as true, { shouldValidate: true })}
          />
          <Text onPress={() => setValue("acceptPrivacyPolicy", !accepted as unknown as true, { shouldValidate: true })}>
            I accept the Privacy Policy
          </Text>
        </View>
        {errors.acceptPrivacyPolicy && (
          <Text style={styles.fieldError}>{errors.acceptPrivacyPolicy.message}</Text>
        )}

        <PrimaryButton onPress={handleSubmit(onSubmit)} loading={isSubmitting} style={{ marginTop: spacing.md }}>
          Create Account
        </PrimaryButton>

        <Divider style={{ marginVertical: spacing.lg }} />
        <Text style={styles.orText}>OR</Text>

        <SecondaryButton icon="google" onPress={onGooglePress} loading={isGoogleLoading} style={{ marginTop: spacing.md }}>
          Continue with Google
        </SecondaryButton>
      </ScrollView>
    </ScreenContainer>
  );
}

function SupplierRegisterForm({
  onSubmit,
  isSubmitting,
  errorMessage,
  isDuplicateEmail,
  onGooglePress,
  isGoogleLoading,
}: {
  onSubmit: (values: SupplierRegisterFormValues) => void;
  isSubmitting: boolean;
} & CommonProps) {
  const {
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<SupplierRegisterFormValues>({
    resolver: zodResolver(supplierRegisterSchema),
    defaultValues: {
      businessName: "",
      ownerName: "",
      email: "",
      password: "",
      confirmPassword: "",
      acceptTerms: undefined as unknown as true,
    },
  });
  const accepted = watch("acceptTerms");

  return (
    <ScreenContainer>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        <Text variant="headlineSmall" style={styles.title}>
          Create Your Supplier Account
        </Text>

        <RegisterError errorMessage={errorMessage} isDuplicateEmail={isDuplicateEmail} />

        <FormTextField control={control} name="businessName" label="Business Name (optional)" />
        <FormTextField control={control} name="ownerName" label="Owner Name" />
        <FormTextField control={control} name="email" label="Email" autoCapitalize="none" keyboardType="email-address" />
        <PasswordField control={control} name="password" label="Password" />
        <PasswordField control={control} name="confirmPassword" label="Confirm Password" />

        <View style={styles.row}>
          <Checkbox
            status={accepted ? "checked" : "unchecked"}
            onPress={() => setValue("acceptTerms", !accepted as unknown as true, { shouldValidate: true })}
          />
          <Text onPress={() => setValue("acceptTerms", !accepted as unknown as true, { shouldValidate: true })}>
            I accept the Terms
          </Text>
        </View>
        {errors.acceptTerms && <Text style={styles.fieldError}>{errors.acceptTerms.message}</Text>}

        <PrimaryButton onPress={handleSubmit(onSubmit)} loading={isSubmitting} style={{ marginTop: spacing.md }}>
          Create Account
        </PrimaryButton>

        <Divider style={{ marginVertical: spacing.lg }} />
        <Text style={styles.orText}>OR</Text>

        <SecondaryButton icon="google" onPress={onGooglePress} loading={isGoogleLoading} style={{ marginTop: spacing.md }}>
          Continue with Google
        </SecondaryButton>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  scrollContent: { paddingBottom: spacing.xl },
  title: { fontWeight: "700", marginTop: spacing.lg, marginBottom: spacing.lg },
  row: { flexDirection: "row", alignItems: "center", marginBottom: spacing.xs },
  fieldError: { color: "#D64545", fontSize: 12, marginBottom: spacing.md, marginLeft: spacing.xl },
  errorText: { color: "#D64545", marginBottom: spacing.xs },
  link: { fontWeight: "600", color: "#0B2447" },
  orText: { textAlign: "center", opacity: 0.6, marginTop: -spacing.lg },
});