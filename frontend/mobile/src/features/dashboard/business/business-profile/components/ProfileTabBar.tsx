import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

export type ProfileTab = "CONTACT" | "BUSINESS" | "VERIFICATION";

const TABS: { key: ProfileTab; label: string }[] = [
  { key: "CONTACT", label: "Contact" },
  { key: "BUSINESS", label: "Business" },
  { key: "VERIFICATION", label: "Verification" },
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
