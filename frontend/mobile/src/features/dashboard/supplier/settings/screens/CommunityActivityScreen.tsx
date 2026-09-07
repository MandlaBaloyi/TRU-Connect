import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { SwitchCard } from "@/components/lists/CardListUI";
import { useSupplierProfileField } from "@/features/dashboard/supplier/my-account/hooks/useSupplierProfileField";
import { LastActiveRow } from "@/features/dashboard/supplier/my-account/components/LastActiveRow";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * Community activity — the supplier's live presence.
 *
 * SEPARATE FROM SUPPLIER VISIBILITY on purpose, even though both
 * answer "what can businesses see about me". Supplier visibility is
 * about the STANDING facts — your photo, your contact details, your
 * trading record; they are the same at 3am as at noon. This is about
 * the LIVE one: are you around right now. A supplier reasons about
 * those differently, and the second question is the one they are
 * likely to revisit, so it gets its own entry rather than being a
 * fourth switch buried under the others.
 *
 * ONE REAL SWITCH, and the preview beneath it. LastActiveRow shows the
 * supplier the exact words a business would read, and keeps showing
 * them with the switch OFF (saying so plainly) — their own activity is
 * not a secret from them, and a preview that vanished when you turned
 * the setting off would make the setting harder to understand, not
 * more private.
 */
export default function CommunityActivityScreen() {
  const theme = useTheme();
  const { profile, saveField, isLoading, refetch } = useSupplierProfileField();

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (!profile) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load your activity settings. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader paddingHorizontal={0}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.body}>
          <SectionHeading
            title="Activity status"
            hint={[
              'Shows businesses roughly when you were last using TruConnect — "Active now", "Active 3 hours ago".',
              "It tells a business you're around and likely to answer, which matters most when they're deciding who to order from today.",
              "Turn it off and businesses see nothing about your activity. You'll still see it yourself.",
            ]}
          />

          <SwitchCard
            label="Show when I was last active"
            description="Businesses viewing your profile can see roughly when you were last online."
            value={profile.showLastActive}
            onValueChange={(showLastActive) => saveField({ showLastActive })}
          />

          <View style={[styles.previewCard, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
            <Text style={[styles.previewLabel, { color: theme.colors.onSurfaceVariant }]}>Right now</Text>
            <LastActiveRow lastActiveAt={profile.lastActiveAt} isShared={profile.showLastActive} />
          </View>

          {/* WHAT THIS SETTING DOES NOT COVER. Connecting is a mutual,
              recorded act — a business you are connected with can see
              that, and turning off a switch cannot un-tell them. Saying
              so here is better than leaving a supplier to assume this
              screen hides more than it does. */}
          <View style={[styles.note, { borderColor: theme.colors.outlineVariant }]}>
            <Text style={[styles.noteTitle, { color: theme.colors.onSurface }]}>What this doesn't hide</Text>
            <Text style={[styles.noteBody, { color: theme.colors.onSurfaceVariant }]}>
              Businesses you're connected with can always see that you're connected, and their orders with you stay in
              their own records either way. This setting covers your activity status only.
            </Text>
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingBottom: spacing.xxl },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  body: { paddingHorizontal: spacing.md, paddingTop: spacing.sm, gap: spacing.md },
  previewCard: {
    borderWidth: 1,
    borderRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    gap: spacing.xs,
  },
  previewLabel: { ...typography.caption, fontWeight: "700", textTransform: "uppercase", letterSpacing: 0.5 },
  note: { borderWidth: 1, borderRadius: radius.lg, padding: spacing.md, gap: spacing.xs, marginTop: spacing.sm },
  noteTitle: { ...typography.body, fontWeight: "700" },
  noteBody: { ...typography.bodySmall, lineHeight: 19 },
});
