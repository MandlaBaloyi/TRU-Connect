import React, { useEffect, useState } from "react";
import { StyleSheet, View, ScrollView } from "react-native";
import { Text, Checkbox, Divider } from "react-native-paper";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
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
import type { UserRole } from "@/features/auth/types";
import { spacing } from "@/theme/spacing";

/**
 * Create Account screen. Renders a different form depending on the role
 * chosen on the Role Selection screen. Deliberately minimal -- only what's
 * needed to create the account and get the user into the app; everything
 * else (SA ID number, registration number, etc.) is collected later in
 * the Business Profile Setup wizard.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 5).
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

  return role === "business" ? (
    <BusinessRegisterForm
      onSubmit={(values) => register.mutate({ role: "business", ...values })}
      isSubmitting={register.isPending}
      onGooglePress={() => googleSignIn.mutate("")}
      isGoogleLoading={googleSignIn.isPending}
    />
  ) : (
    <SupplierRegisterForm
      onSubmit={(values) => register.mutate({ role: "supplier", ...values })}
      isSubmitting={register.isPending}
      onGooglePress={() => googleSignIn.mutate("")}
      isGoogleLoading={googleSignIn.isPending}
    />
  );
}

interface GoogleProps {
  onGooglePress: () => void;
  isGoogleLoading: boolean;
}

function BusinessRegisterForm({
  onSubmit,
  isSubmitting,
  onGooglePress,
  isGoogleLoading,
}: {
  onSubmit: (values: BusinessRegisterFormValues) => void;
  isSubmitting: boolean;
} & GoogleProps) {
  const { control, handleSubmit, watch, setValue } = useForm<BusinessRegisterFormValues>({
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
        <FormTextField control={control} name="firstName" label="First Name" />
        <FormTextField control={control} name="lastName" label="Last Name" />
        <FormTextField control={control} name="businessName" label="Business Name (optional)" />
        <FormTextField control={control} name="email" label="Email Address" autoCapitalize="none" keyboardType="email-address" />
        <PasswordField control={control} name="password" label="Password" />
        <PasswordField control={control} name="confirmPassword" label="Confirm Password" />

        <View style={styles.row}>
          <Checkbox
            status={accepted ? "checked" : "unchecked"}
            onPress={() => setValue("acceptPrivacyPolicy", !accepted as unknown as true)}
          />
          <Text onPress={() => setValue("acceptPrivacyPolicy", !accepted as unknown as true)}>
            I accept the Privacy Policy
          </Text>
        </View>

        <PrimaryButton onPress={handleSubmit(onSubmit)} loading={isSubmitting} style={{ marginTop: spacing.md }}>
          Create Account
        </PrimaryButton>

        <Divider style={{ marginVertical: spacing.lg }} />
        <Text style={styles.orText}>OR</Text>

        <SecondaryButton
          icon="google"
          onPress={onGooglePress}
          loading={isGoogleLoading}
          style={{ marginTop: spacing.md }}
        >
          Continue with Google
        </SecondaryButton>
      </ScrollView>
    </ScreenContainer>
  );
}

function SupplierRegisterForm({
  onSubmit,
  isSubmitting,
  onGooglePress,
  isGoogleLoading,
}: {
  onSubmit: (values: SupplierRegisterFormValues) => void;
  isSubmitting: boolean;
} & GoogleProps) {
  const { control, handleSubmit, watch, setValue } = useForm<SupplierRegisterFormValues>({
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
        <FormTextField control={control} name="businessName" label="Business Name (optional)" />
        <FormTextField control={control} name="ownerName" label="Owner Name" />
        <FormTextField control={control} name="email" label="Email" autoCapitalize="none" keyboardType="email-address" />
        <PasswordField control={control} name="password" label="Password" />
        <PasswordField control={control} name="confirmPassword" label="Confirm Password" />

        <View style={styles.row}>
          <Checkbox
            status={accepted ? "checked" : "unchecked"}
            onPress={() => setValue("acceptTerms", !accepted as unknown as true)}
          />
          <Text onPress={() => setValue("acceptTerms", !accepted as unknown as true)}>I accept the Terms</Text>
        </View>

        <PrimaryButton onPress={handleSubmit(onSubmit)} loading={isSubmitting} style={{ marginTop: spacing.md }}>
          Create Account
        </PrimaryButton>

        <Divider style={{ marginVertical: spacing.lg }} />
        <Text style={styles.orText}>OR</Text>

        <SecondaryButton
          icon="google"
          onPress={onGooglePress}
          loading={isGoogleLoading}
          style={{ marginTop: spacing.md }}
        >
          Continue with Google
        </SecondaryButton>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  scrollContent: { paddingBottom: spacing.xl },
  title: { fontWeight: "700", marginTop: spacing.lg, marginBottom: spacing.lg },
  row: { flexDirection: "row", alignItems: "center", marginBottom: spacing.md },
  orText: { textAlign: "center", opacity: 0.6, marginTop: -spacing.lg },
});