import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { InfoHint } from "@/components/ui/InfoHint";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { SETUP_STEP_ORDER } from "../types";
import type { SetupStepId } from "../types";

/**
 * The shape every setup step shares: where you are, what is being
 * asked, and one way forward.
 *
 * ── THE STEP INDICATOR IS LOUD NOW ──────────────────────────────
 *
 * It was three small dots with "Step 1 of 3" in caption grey
 * underneath, and Mandla could not see it: "make the step clear at the
 * top". Three reasons it failed. Dots are an ambiguous shape -- they
 * read as a carousel, which is something you swipe, not something you
 * finish. They were 8px against a 22px heading directly below, so the
 * eye skipped them entirely. And the count sat UNDER them in the
 * quietest type on the screen.
 *
 * It is now three SEGMENTS -- a bar broken into the number of steps --
 * with the count above it in small uppercase. A segmented bar is the
 * one progress shape nobody misreads, and it answers "how much is
 * left" without being counted.
 *
 * ── THE EXPLANATION MOVED INTO AN ⓘ ─────────────────────────────
 *
 * Every step carried a grey paragraph under its heading saying what
 * the answer would change. Mandla: "Remove the subheading... put the
 * information icon somewhere to explain why exactly I'm collecting
 * this data."
 *
 * He is right, and the codebase had already learned this once -- see
 * InfoHint's own docstring, written when supplier screens had grown a
 * paragraph under every section: "a supplier scrolled through more
 * explanation than actual profile". A signup flow is the worst place
 * to repeat it, because the reader has no investment yet and every
 * line of grey text is a line between them and being finished.
 *
 * THE PROMISE STILL HAS TO BE MAKEABLE, THOUGH. The rule
 * tell_us_what_you_buy follows -- only ask for what will visibly
 * change the next screen, and SAY what it will change -- is not
 * satisfied by hiding the answer. So the ⓘ sits against the question
 * itself, and its body is exactly the sentence that used to be
 * printed. Opt-in rather than absent: whoever wants to know why can
 * find out in one tap, and whoever does not never pays for it.
 *
 * NO BACK BUTTON AND NO HEADER. The steps are independent writes, so
 * "back" would mean re-saving a section that is already saved -- and a
 * flow with a gate behind it that a person can walk backwards out of
 * is a way to land on a blank screen behind their own dashboard.
 */
export function SetupStepScaffold({
  step,
  title,
  why,
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
  /** Why this is being asked, behind the ⓘ beside the question. One or
   *  more short paragraphs. Required -- a question with no statable
   *  reason should not be on a mandatory signup screen at all. */
  why: string | string[];
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
    <ScreenContainer paddingHorizontal={0}>
      <View style={styles.header}>
        <Text style={[styles.stepCount, { color: theme.colors.primary }]}>
          STEP {index + 1} OF {SETUP_STEP_ORDER.length}
        </Text>
        <View style={styles.track}>
          {SETUP_STEP_ORDER.map((id, i) => (
            <View
              key={id}
              style={[
                styles.segment,
                {
                  backgroundColor:
                    i <= index ? theme.colors.primary : theme.colors.outlineVariant,
                },
              ]}
            />
          ))}
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.titleRow}>
          <Text style={[styles.title, { color: theme.colors.onSurface }]}>{title}</Text>
          <InfoHint title={title} body={why} size={20} accessibilityLabel="Why we ask this" />
        </View>

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
  header: { paddingHorizontal: spacing.md, paddingTop: spacing.md, gap: spacing.xs },
  stepCount: {
    ...typography.caption,
    fontWeight: "800",
    letterSpacing: 1.2,
  },
  track: { flexDirection: "row", gap: spacing.xs },
  // FLEX 1 EACH, so the bar always spans the width whatever the step
  // count becomes -- a fourth step should not need a new number here.
  segment: { flex: 1, height: 6, borderRadius: 3 },
  content: { padding: spacing.md, paddingTop: spacing.lg, paddingBottom: spacing.xl, gap: spacing.lg },
  // The ⓘ sits ON the question rather than in the corner, because it
  // explains THIS question and a floating corner icon explains the
  // screen.
  titleRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  title: { ...typography.h1, fontWeight: "800", flexShrink: 1 },
  body: { gap: spacing.lg },
  error: { ...typography.bodySmall },
  // PINNED, not at the end of the scroll -- a Continue button below a
  // long answer list is a button people report as missing.
  footer: {
    padding: spacing.md,
    gap: spacing.sm,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
});
