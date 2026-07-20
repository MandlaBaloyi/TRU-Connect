import React from "react";
import { View, StyleSheet } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { spacing } from "@/theme/spacing";

interface ProgressStepperProps {
  totalSteps: number;
  currentStep: number; // 1-indexed
  stepLabels?: string[];
}

/**
 * Visible step indicator for multi-step forms.
 * Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 9 (Forms) and
 * docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Business Profile Setup
 * Wizard, 5 steps).
 */
export function ProgressStepper({ totalSteps, currentStep, stepLabels }: ProgressStepperProps) {
  const theme = useTheme();
  return (
    <View>
      <View style={styles.row}>
        {Array.from({ length: totalSteps }).map((_, i) => {
          const stepIndex = i + 1;
          const isComplete = stepIndex < currentStep;
          const isActive = stepIndex === currentStep;
          return (
            <View
              key={i}
              style={[
                styles.segment,
                {
                  backgroundColor:
                    isComplete || isActive ? theme.colors.primary : theme.colors.outline,
                },
              ]}
            />
          );
        })}
      </View>
      {stepLabels && (
        <Text variant="bodySmall" style={{ marginTop: spacing.sm, color: theme.colors.onSurfaceVariant }}>
          Step {currentStep} of {totalSteps}: {stepLabels[currentStep - 1]}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: 6 },
  segment: { flex: 1, height: 6, borderRadius: 3 },
});
