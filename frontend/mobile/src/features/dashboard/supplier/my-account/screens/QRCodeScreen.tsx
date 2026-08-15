import React, { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { MyCodeTab } from "../components/MyCodeTab";
import { ScanCodeTab } from "../components/ScanCodeTab";

const TABS = [
  { key: "MY_CODE", label: "My code" },
  { key: "SCAN_CODE", label: "Scan code" },
] as const;

/**
 * QR code screen — "My Code" / "Scan Code" tabs, matching the
 * WhatsApp reference this was based on. Same tab-row visual pattern
 * already used for Community's For You/Following (word-hugging
 * underline, not full-width) — reused here rather than invented fresh.
 *
 * MyCodeTab is genuinely real (see its own docstring); ScanCodeTab's
 * camera and QR detection are genuinely real too — only resolving a
 * scanned code against a real account isn't, and that tab says so
 * plainly rather than pretending otherwise.
 */
export default function QRCodeScreen() {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState<(typeof TABS)[number]["key"]>("MY_CODE");

  return (
    <ScreenContainer hasNativeHeader paddingHorizontal={0}>
      <View style={[styles.tabsRow, { borderBottomColor: theme.colors.outlineVariant }]}>
        {TABS.map((tab) => {
          const selected = tab.key === activeTab;
          return (
            <Pressable
              key={tab.key}
              onPress={() => setActiveTab(tab.key)}
              style={styles.tab}
              accessibilityRole="tab"
              accessibilityState={{ selected }}
              accessibilityLabel={tab.label}
            >
              <Text
                style={[styles.tabLabel, { color: selected ? theme.colors.primary : theme.colors.onSurfaceVariant }]}
              >
                {tab.label}
              </Text>
              {selected && <View style={[styles.tabIndicator, { backgroundColor: theme.colors.primary }]} />}
            </Pressable>
          );
        })}
      </View>

      <View style={styles.body}>{activeTab === "MY_CODE" ? <MyCodeTab /> : <ScanCodeTab />}</View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  tabsRow: { flexDirection: "row", borderBottomWidth: StyleSheet.hairlineWidth },
  tab: { flex: 1, alignItems: "center", paddingVertical: spacing.sm },
  tabLabel: { ...typography.body, fontWeight: "700" },
  tabIndicator: { height: 2, width: 40, borderRadius: 1, marginTop: spacing.xs },
  body: { flex: 1 },
});
