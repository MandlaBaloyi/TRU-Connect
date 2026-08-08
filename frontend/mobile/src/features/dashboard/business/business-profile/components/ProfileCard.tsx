import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Check } from "lucide-react-native";

import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  title: string;
  isComplete?: boolean;
  children: React.ReactNode;
}

/** Plain title + content — NO card border, background, or padding.
 *  Per direct feedback, the bordered card shell was taking up too much
 *  space for what's a single small piece of information (e.g. three
 *  contact lines). The tabs already separate Contact/Business/
 *  Verification, so a card boundary per section was redundant weight
 *  on top of that. Multiple sections on the Business tab are told
 *  apart with a plain divider instead (see BusinessProfileScreen). */
export function ProfileCard({ title, isComplete, children }: Props) {
  const theme = useTheme();
  return (
    <View style={styles.wrapper}>
      <View style={styles.titleRow}>
        <Text style={[styles.title, { color: theme.colors.onSurface }]}>{title}</Text>
        {isComplete && (
          <View style={[styles.badge, { backgroundColor: theme.colors.secondaryContainer }]}>
            <Check size={12} color={theme.colors.secondary} strokeWidth={3} />
          </View>
        )}
      </View>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: spacing.xs },
  titleRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs, marginBottom: spacing.xs },
  title: { ...typography.body, fontWeight: "700" },
  badge: { width: 18, height: 18, borderRadius: 9, alignItems: "center", justifyContent: "center" },
});
