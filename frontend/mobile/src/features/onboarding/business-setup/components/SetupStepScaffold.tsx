import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { SETUP_STEP_ORDER } from "../types";
import type { SetupStepId } from "../types";

/**
 * The shape every setup step shares: where you are, what is being
 * asked, what it changes, and one way forward.
 *
 * THE PROMISE LINE IS NOT DECORATION. It is the rule the feed's own
 * "tell us what you buy" rail already follows, quoted in that
 * section's docstring:
 *
 *     ONLY ASK FOR WHAT WILL VISIBLY CHANGE THE NEXT SCREEN, AND SAY
 *     EXACTLY WHAT IT WILL CHANGE.
 *
 * A signup flow that asks those same questions without that same
 * sentence is a worse version of a screen this app already got right —
 * it turns "help us help you" into an interview, which is how a person
 * decides the app is for somebody else's benefit.
 *
 * THREE DOTS, NOT A PERCENTAGE. Three is small enough to count, and a
 * percentage invites the question "what happens at 60%" — which has no
 * answer here, because a step is answered or it is not.
 *
 * NO BACK BUTTON AND NO HEADER. Two reasons, and the second is the
 * real one: the steps are independent writes, so "back" would mean
 * re-saving a section that is already saved; and a stack a person can
 * walk backwards out of, on a flow with a gate behind it, is a way to
 * end up on a blank screen behind their own dashboard. Changing an
 * answer later is what My Business is for, and it stays in the More
 * tab exactly so it can be.
 */
export function SetupStepScaffold({
  step,
  title,
  promise,
  children,
  primaryLabel = "Continue",
  onPrimary,
  primaryDisabled,
  isSaving,
  error,
  secondary,
}: {
  step: SetupStepId;
  title: string;
  /** One sentence naming what this answer changes. Required. */
  promise: string;
  children: React.ReactNode;
  primaryLabel?: string;
  onPrimary: () => void;
  primaryDisabled?: boolean;
  isSaving?: boolean;
  error?: string | null;
  /** The skip, on the one step that has one. */
  secondary?: React.ReactNode;
}) {
  const theme = useTheme();
  const index = SETUP_STEP_ORDER.indexOf(step);

  return (
    // paddingHorizontal={0} because the footer's top border has to
    // span the full width -- with the container's own md padding it
    // would stop short at both ends and read as a stray line rather
    // than as the edge of a bar.
    <ScreenContainer paddingHorizontal={0}>
      <View style={styles.header}>
        <View style={styles.dots}>
          {SETUP_STEP_ORDER.map((id, i) => (
            <View
              key={id}
              style={[
                styles.dot,
                {
                  backgroundColor: i <= index ? theme.colors.primary : theme.colors.outlineVariant,
                  // The current step is wider rather than a different
                  // colour: "where I am" and "how far I have come" are
                  // two facts, and one colour cannot carry both.
                  width: i === index ? 24 : 8,
                },
              ]}
            />
          ))}
        </View>
        <Text style={[styles.stepCount, { color: theme.colors.onSurfaceVariant }]}>
          Step {index + 1} of {SETUP_STEP_ORDER.length}
        </Text>
      </View>

      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text style={[styles.title, { color: theme.colors.onSurface }]}>{title}</Text>
        <Text style={[styles.promise, { color: theme.colors.onSurfaceVariant }]}>{promise}</Text>

        <View style={styles.body}>{children}</View>

        {error ? <Text style={[styles.error, { color: theme.colors.error }]}>{error}</Text> : null}
      </ScrollView>

      <View style={[styles.footer, { borderTopColor: theme.colors.outlineVariant }]}>
        <PrimaryButton onPress={onPrimary} loading={isSaving} disabled={primaryDisabled || isSaving}>
          {primaryLabel}
        </PrimaryButton>
        {secondary}
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: { paddingHorizontal: spacing.md, paddingTop: spacing.md, gap: spacing.sm },
  dots: { flexDirection: "row", gap: spacing.xs, alignItems: "center" },
  dot: { height: 8, borderRadius: 4 },
  stepCount: { ...typography.caption },
  content: { padding: spacing.md, paddingBottom: spacing.xl, gap: spacing.xs },
  title: { ...typography.h1, fontWeight: "800" },
  promise: { ...typography.body, marginBottom: spacing.md },
  body: { gap: spacing.lg },
  error: { ...typography.bodySmall, marginTop: spacing.md },
  // PINNED, not at the end of the scroll. On step one the chip list is
  // long enough to scroll, and a Continue button somewhere below
  // seventeen categories is a button people report as missing.
  footer: {
    padding: spacing.md,
    gap: spacing.sm,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
});
