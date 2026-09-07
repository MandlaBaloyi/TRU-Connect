import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Clock } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { Hero } from "@/components/lists/CardListUI";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  /** What this feature WILL do, in plain language. Required — a
   *  coming-soon screen that just says "coming soon" and nothing else
   *  wastes the tap. The point is that the business owner leaves
   *  understanding what to expect. */
  description: string;
  /** Optional concrete examples of what the feature will cover. */
  examples?: string[];
}

/**
 * The honest "not built yet" screen — now built on the shared Hero
 * component for visual consistency with the rest of Settings and
 * Account Security. Every COMING_SOON setting routes here rather than
 * showing a switch that silently does nothing — see settings/types.ts's
 * SettingStatus for the full reasoning.
 */
export function ComingSoonScreen({ description, examples }: Props) {
  const theme = useTheme();
  const router = useRouter();

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <Hero icon={<Clock size={28} color={theme.colors.primary} strokeWidth={1.8} />} title="Coming soon" description={description} />

        {examples && examples.length > 0 && (
          <View style={[styles.examplesCard, { backgroundColor: theme.colors.surfaceVariant }]}>
            {examples.map((example) => (
              <View key={example} style={styles.exampleRow}>
                <View style={[styles.bullet, { backgroundColor: theme.colors.onSurfaceVariant }]} />
                <Text style={[styles.exampleText, { color: theme.colors.onSurfaceVariant }]}>{example}</Text>
              </View>
            ))}
          </View>
        )}

        <PrimaryButton onPress={() => router.back()}>Got it</PrimaryButton>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, gap: spacing.lg },
  examplesCard: { borderRadius: radius.lg, padding: spacing.md, gap: spacing.sm },
  exampleRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  bullet: { width: 4, height: 4, borderRadius: 2 },
  exampleText: { ...typography.body, flexShrink: 1 },
});
