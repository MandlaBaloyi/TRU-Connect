import React from "react";
import { StyleSheet } from "react-native";
import { Text } from "react-native-paper";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { FormTextField } from "@/components/forms/FormTextField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SecondaryButton } from "@/components/ui/SecondaryButton";
import { ProgressStepper } from "@/components/ui/ProgressStepper";
import { ScreenHeader } from "@/components/navigation/ScreenHeader";
import { ownerInfoSchema, OwnerInfoFormValues } from "@/features/business/schemas/businessSchemas";
import { useBusinessProfileWizard } from "@/features/business/hooks/useBusinessProfileWizard";
import { spacing } from "@/theme/spacing";

const STEP_LABELS = ["Business Info", "Owner Info", "Trading Info", "Documents", "Review"];

/**
 * Step 2 - Owner Information.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 7, Step 2).
 */
export default function OwnerInfoStep() {
  const router = useRouter();
  const { ownerInfo, setOwnerInfo } = useBusinessProfileWizard();
  const { control, handleSubmit } = useForm<OwnerInfoFormValues>({
    resolver: zodResolver(ownerInfoSchema),
    defaultValues: {
      ownerName: ownerInfo.ownerName ?? "",
      saIdNumber: ownerInfo.saIdNumber ?? "",
      phoneNumber: ownerInfo.phoneNumber ?? "",
      email: ownerInfo.email ?? "",
    },
  });

  const onNext = (values: OwnerInfoFormValues) => {
    setOwnerInfo(values);
    router.push("/(business)/profile-setup/step-3-trading-info");
  };

  return (
    <ScreenContainer>
      <ScreenHeader onBack={() => router.back()} />
      <ProgressStepper totalSteps={5} currentStep={2} stepLabels={STEP_LABELS} />
      <Text variant="headlineSmall" style={styles.title}>
        Owner Information
      </Text>

      <FormTextField control={control} name="ownerName" label="Owner Name" />
      <FormTextField control={control} name="saIdNumber" label="ID Number" keyboardType="number-pad" />
      <FormTextField control={control} name="phoneNumber" label="Phone" keyboardType="phone-pad" />
      <FormTextField control={control} name="email" label="Email" autoCapitalize="none" keyboardType="email-address" />

      <PrimaryButton onPress={handleSubmit(onNext)} style={{ marginTop: spacing.md }}>
        Continue
      </PrimaryButton>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontWeight: "700", marginVertical: spacing.lg },
});
