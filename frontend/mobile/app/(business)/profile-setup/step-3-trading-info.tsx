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
import { ScreenHeader } from "@/components/navigation/ScreenHeader";
import { tradingInfoSchema, TradingInfoFormValues } from "@/features/business/schemas/businessSchemas";
import { useBusinessProfileWizard } from "@/features/business/hooks/useBusinessProfileWizard";
import { spacing } from "@/theme/spacing";

const STEP_LABELS = ["Business Info", "Owner Info", "Trading Info", "Documents", "Review"];

/**
 * Step 3 - Trading Information.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 7, Step 3)
 * and docs/07_DATA_AND_TRUST_ENGINE.txt (this data seeds the initial
 * Digital Business Profile / Business Health Score baseline).
 */
export default function TradingInfoStep() {
  const router = useRouter();
  const { tradingInfo, setTradingInfo } = useBusinessProfileWizard();
  const { control, handleSubmit } = useForm<TradingInfoFormValues>({
    resolver: zodResolver(tradingInfoSchema),
    defaultValues: {
      monthlyRevenue: tradingInfo.monthlyRevenue ?? "",
      customersPerMonth: tradingInfo.customersPerMonth ?? "",
      averageTransaction: tradingInfo.averageTransaction ?? "",
      primarySupplier: tradingInfo.primarySupplier ?? "",
    },
  });

  const onNext = (values: TradingInfoFormValues) => {
    setTradingInfo(values);
    router.push("/(business)/profile-setup/step-4-documents");
  };

  return (
    <ScreenContainer>
      <ScreenHeader onBack={() => router.back()} />
      <ProgressStepper totalSteps={5} currentStep={3} stepLabels={STEP_LABELS} />
      <Text variant="headlineSmall" style={styles.title}>
        Trading Information
      </Text>

      <FormTextField control={control} name="monthlyRevenue" label="Monthly Revenue" keyboardType="numeric" />
      <FormTextField control={control} name="customersPerMonth" label="Customers Per Month" keyboardType="number-pad" />
      <FormTextField control={control} name="averageTransaction" label="Average Transaction" keyboardType="numeric" />
      <FormTextField control={control} name="primarySupplier" label="Primary Supplier (optional)" />

      <PrimaryButton onPress={handleSubmit(onNext)} style={{ marginTop: spacing.md }}>
        Continue
      </PrimaryButton>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontWeight: "700", marginVertical: spacing.lg },
});
