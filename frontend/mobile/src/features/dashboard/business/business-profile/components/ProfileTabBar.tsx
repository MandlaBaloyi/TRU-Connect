import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

export type ProfileTab = "CONTACT" | "BUSINESS";

/** VERIFICATION WAS A THIRD TAB AND IS GONE (V2_18 Part 2). It showed
 *  four boxes: two that could never tick (no email-verification flow;
 *  two columns nothing ever wrote), and one that could never fail to
 *  tick (every route on this screen is @fully_authenticated, so the
 *  OTP is already done by definition). A checklist where no row can
 *  change is not a checklist -- and on a business it implied a review
 *  that does not happen and should not. The completion bar above this
 *  bar is the honest version of the same idea. */
const TABS: { key: ProfileTab; label: string }[] = [
  { key: "CONTACT", label: "Contact" },
  { key: "BUSINESS", label: "Business" },
];

interface Props {
  active: ProfileTab;
  onChange: (tab: ProfileTab) => void;
}

/** Fixed, always visible — does not scroll away with the tab content
 *  below it. Underline under the active tab shows where you are. */
export function ProfileTabBar({ active, onChange }: Props) {
  const theme = useTheme();
  return (
    <View style={[styles.row, { borderBottomColor: theme.colors.outline, backgroundColor: theme.colors.background }]}>
      {TABS.map((tab) => {
        const selected = tab.key === active;
        return (
          <Pressable
            key={tab.key}
            onPress={() => onChange(tab.key)}
            style={styles.tab}
            accessibilityRole="tab"
            accessibilityState={{ selected }}
            accessibilityLabel={tab.label}
          >
            <Text style={[styles.label, { color: selected ? theme.colors.primary : theme.colors.onSurfaceVariant }]}>
              {tab.label}
            </Text>
            <View style={[styles.underline, { backgroundColor: selected ? theme.colors.primary : "transparent" }]} />
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", borderBottomWidth: StyleSheet.hairlineWidth },
  tab: { flex: 1, alignItems: "center", paddingVertical: spacing.sm, gap: spacing.xs },
  label: { ...typography.body, fontWeight: "700" },
  underline: { height: 3, width: "60%", borderRadius: 2 },
});
