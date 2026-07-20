import React from "react";
import { StyleSheet } from "react-native";
import { Text } from "react-native-paper";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { FormTextField } from "@/components/forms/FormTextField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ProgressStepper } from "@/components/ui/ProgressStepper";
import { businessInfoSchema, BusinessInfoFormValues } from "@/features/business/schemas/businessSchemas";
import { useBusinessProfileWizard } from "@/features/business/hooks/useBusinessProfileWizard";
import { spacing } from "@/theme/spacing";

const STEP_LABELS = ["Business Info", "Owner Info", "Trading Info", "Documents", "Review"];

/**
 * Step 1 - Business Information.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 7, Step 1)
 * and docs/04_DATABASE_DESIGN.txt Section 4.2 (businesses,
 * business_addresses).
 */
export default function BusinessInfoStep() {
  const router = useRouter();
  const { businessInfo, setBusinessInfo } = useBusinessProfileWizard();
  const { control, handleSubmit } = useForm<BusinessInfoFormValues>({
    resolver: zodResolver(businessInfoSchema),
    defaultValues: {
      businessName: businessInfo.businessName ?? "",
      tradingName: businessInfo.tradingName ?? "",
      businessType: businessInfo.businessType ?? "",
      industry: businessInfo.industry ?? "",
      yearsOperating: businessInfo.yearsOperating ?? "",
      addressLine: businessInfo.addressLine ?? "",
    },
  });

  const onNext = (values: BusinessInfoFormValues) => {
    setBusinessInfo(values);
    router.push("/(business)/profile-setup/step-2-owner-info");
  };

  return (
    <ScreenContainer>
      <ProgressStepper totalSteps={5} currentStep={1} stepLabels={STEP_LABELS} />
      <Text variant="headlineSmall" style={styles.title}>
        Business Information
      </Text>

      <FormTextField control={control} name="businessName" label="Business Name" />
      <FormTextField control={control} name="tradingName" label="Trading Name (optional)" />
      <FormTextField control={control} name="businessType" label="Business Type" />
      <FormTextField control={control} name="industry" label="Industry" />
      <FormTextField control={control} name="yearsOperating" label="Years Operating" keyboardType="number-pad" />
      <FormTextField control={control} name="addressLine" label="Business Address" />

      <PrimaryButton onPress={handleSubmit(onNext)} style={{ marginTop: spacing.md }}>
        Continue
      </PrimaryButton>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontWeight: "700", marginVertical: spacing.lg },
});
