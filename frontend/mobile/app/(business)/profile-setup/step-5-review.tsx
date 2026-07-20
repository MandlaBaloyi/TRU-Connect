import React from "react";
import { StyleSheet, ScrollView, View } from "react-native";
import { Text, Divider } from "react-native-paper";
import { useRouter } from "expo-router";
import { useMutation } from "@tanstack/react-query";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ProgressStepper } from "@/components/ui/ProgressStepper";
import { ScreenHeader } from "@/components/navigation/ScreenHeader";
import { AppCard } from "@/components/cards/AppCard";
import { LoadingOverlay } from "@/components/feedback/LoadingOverlay";
import { useBusinessProfileWizard } from "@/features/business/hooks/useBusinessProfileWizard";
import { businessApi } from "@/features/business/api/businessApi";
import { spacing } from "@/theme/spacing";

const STEP_LABELS = ["Business Info", "Owner Info", "Trading Info", "Documents", "Review"];

/**
 * Step 5 - Review & Submit.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 7, Step 5)
 * and docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.2
 * (PUT /businesses/me).
 */
export default function ReviewStep() {
  const router = useRouter();
  const wizard = useBusinessProfileWizard();

  const submit = useMutation({
    mutationFn: () => businessApi.submitProfileSetup(wizard),
    onSuccess: () => {
      wizard.reset();
      router.replace("/(dashboard)/home");
    },
  });

  return (
    <ScreenContainer>
      <ScreenHeader onBack={() => router.back()} />
      <ProgressStepper totalSteps={5} currentStep={5} stepLabels={STEP_LABELS} />
      <Text variant="headlineSmall" style={styles.title}>
        Review Your Information
      </Text>

      <ScrollView showsVerticalScrollIndicator={false}>
        <ReviewSection title="Business Information">
          <ReviewRow label="Business Name" value={wizard.businessInfo.businessName} />
          <ReviewRow label="Trading Name" value={wizard.businessInfo.tradingName} />
          <ReviewRow label="Business Type" value={wizard.businessInfo.businessType} />
          <ReviewRow label="Industry" value={wizard.businessInfo.industry} />
          <ReviewRow label="Years Operating" value={wizard.businessInfo.yearsOperating} />
          <ReviewRow label="Address" value={wizard.businessInfo.addressLine} />
        </ReviewSection>

        <ReviewSection title="Owner Information">
          <ReviewRow label="Owner Name" value={wizard.ownerInfo.ownerName} />
          <ReviewRow label="ID Number" value={wizard.ownerInfo.saIdNumber} />
          <ReviewRow label="Phone" value={wizard.ownerInfo.phoneNumber} />
          <ReviewRow label="Email" value={wizard.ownerInfo.email} />
        </ReviewSection>

        <ReviewSection title="Trading Information">
          <ReviewRow label="Monthly Revenue" value={wizard.tradingInfo.monthlyRevenue} />
          <ReviewRow label="Customers Per Month" value={wizard.tradingInfo.customersPerMonth} />
          <ReviewRow label="Average Transaction" value={wizard.tradingInfo.averageTransaction} />
          <ReviewRow label="Primary Supplier" value={wizard.tradingInfo.primarySupplier} />
        </ReviewSection>
      </ScrollView>

      {submit.isError && (
        <Text style={styles.errorText}>
          We couldn't submit your profile. Please check your connection and try again.
        </Text>
      )}

      <PrimaryButton
        onPress={() => submit.mutate()}
        loading={submit.isPending}
        style={{ marginTop: spacing.md }}
      >
        Submit
      </PrimaryButton>

      <LoadingOverlay visible={submit.isPending} label="Submitting your profile..." />
    </ScreenContainer>
  );
}

function ReviewSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <AppCard style={{ marginBottom: spacing.md }}>
      <Text variant="titleMedium" style={{ fontWeight: "700", marginBottom: spacing.sm }}>
        {title}
      </Text>
      <Divider style={{ marginBottom: spacing.sm }} />
      {children}
    </AppCard>
  );
}

function ReviewRow({ label, value }: { label: string; value?: string }) {
  return (
    <View style={styles.reviewRow}>
      <Text style={styles.reviewLabel}>{label}</Text>
      <Text style={styles.reviewValue}>{value || "-"}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  title: { fontWeight: "700", marginVertical: spacing.lg },
  reviewRow: { flexDirection: "row", justifyContent: "space-between", marginBottom: spacing.xs },
  reviewLabel: { opacity: 0.6 },
  reviewValue: { fontWeight: "600" },
  errorText: { color: "#D64545", marginTop: spacing.sm },
});
