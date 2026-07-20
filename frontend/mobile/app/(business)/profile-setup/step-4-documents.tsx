import React from "react";
import { StyleSheet, View } from "react-native";
import { Text, List } from "react-native-paper";
import { useRouter } from "expo-router";
import { IdCard, Images, Receipt, Landmark } from "lucide-react-native";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ProgressStepper } from "@/components/ui/ProgressStepper";
import { ScreenHeader } from "@/components/navigation/ScreenHeader";
import { AppCard } from "@/components/cards/AppCard";
import { spacing } from "@/theme/spacing";

const STEP_LABELS = ["Business Info", "Owner Info", "Trading Info", "Documents", "Review"];

/**
 * Step 4 - Documents.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 7, Step 4)
 * and docs/04_DATABASE_DESIGN.txt Section 4.2 (business_documents) /
 * Section 4.6 (verification_documents).
 *
 * Document upload (image picker) integration is stubbed here with
 * placeholder rows; wire up an image picker + businessApi.uploadDocument
 * in the next implementation pass.
 */
export default function DocumentsStep() {
  const router = useRouter();

  const onNext = () => {
    router.push("/(business)/profile-setup/step-5-review");
  };

  return (
    <ScreenContainer>
      <ScreenHeader onBack={() => router.back()} />
      <ProgressStepper totalSteps={5} currentStep={4} stepLabels={STEP_LABELS} />
      <Text variant="headlineSmall" style={styles.title}>
        Documents
      </Text>

      <AppCard style={{ marginBottom: spacing.md }}>
        <List.Item title="ID Copy" description="Required" left={() => <IdCard size={22} />} />
      </AppCard>
      <AppCard style={{ marginBottom: spacing.md }}>
        <List.Item title="Business Photos" description="Required" left={() => <Images size={22} />} />
      </AppCard>
      <AppCard style={{ marginBottom: spacing.md }}>
        <List.Item title="Trading Proof" description="Required" left={() => <Receipt size={22} />} />
      </AppCard>
      <AppCard style={{ marginBottom: spacing.md }}>
        <List.Item title="Bank Statement" description="Optional" left={() => <Landmark size={22} />} />
      </AppCard>

      <View style={{ flex: 1 }} />

      <PrimaryButton onPress={onNext} style={{ marginTop: spacing.md }}>
        Continue
      </PrimaryButton>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontWeight: "700", marginVertical: spacing.lg },
});
