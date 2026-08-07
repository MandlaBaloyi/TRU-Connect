/**
 * AutoClearAccordion — collapsed by default so it doesn't compete with
 * the TODAY figure for attention on the Balances screen. Wording says
 * "move to Trash", never "clear" or "delete" alone — this is a
 * recoverable action (7-day Trash window), and the copy should never
 * make the shop owner think their records are gone for good.
 *
 * Reused for both COMPLETED and CANCELLED scopes (see AutoClearScope's
 * docstring in types.ts) — same component, different title/copy and an
 * independent setting each.
 *
 * PRESETS KEPT SHORT (Off/5 min/15 min) — anything longer is what the
 * Custom row is for, rather than growing this list.
 */

import React, { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useTheme } from "react-native-paper";
import { ChevronDown, ChevronUp } from "lucide-react-native";

import type { AutoClearDuration, AutoClearScope, AutoClearSetting } from "../types";
import { AUTO_CLEAR_DURATION_LABELS } from "../types";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  scope: AutoClearScope;
  setting: AutoClearSetting;
  onChange: (setting: AutoClearSetting) => Promise<unknown>;
}

const PRESET_OPTIONS: AutoClearDuration[] = ["OFF", "5_MIN", "15_MIN"];

function titleFor(scope: AutoClearScope): string {
  return scope === "COMPLETED"
    ? "Automatically move completed orders to Trash"
    : "Automatically move cancelled orders to Trash";
}

function descriptionFor(scope: AutoClearScope): string {
  const label = scope === "COMPLETED" ? "Completed" : "Cancelled";
  return `${label} orders will be moved to Trash after the selected time, and can still be restored from there for 7 days.`;
}

export function AutoClearAccordion({ scope, setting, onChange }: Props) {
  const theme = useTheme();
  const [expanded, setExpanded] = useState(false);
  const [customHoursText, setCustomHoursText] = useState(
    setting.duration === "CUSTOM" && setting.customHours ? String(setting.customHours) : ""
  );
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [justSaved, setJustSaved] = useState(false);

  const summary =
    setting.duration === "CUSTOM" && setting.customHours
      ? `${setting.customHours} hr`
      : AUTO_CLEAR_DURATION_LABELS[setting.duration];

  const applyChange = async (next: AutoClearSetting) => {
    setIsSaving(true);
    setSaveError(null);
    setJustSaved(false);
    try {
      await onChange(next);
      setJustSaved(true);
      setTimeout(() => setJustSaved(false), 2000);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "Could not save this setting. Try again.");
    } finally {
      setIsSaving(false);
    }
  };

  const handlePreset = (duration: AutoClearDuration) => {
    applyChange({ duration });
  };

  const handleSetCustom = () => {
    const hours = Number.parseFloat(customHoursText);
    if (!hours || hours <= 0) {
      setSaveError("Enter a number of hours greater than 0.");
      return;
    }
    applyChange({ duration: "CUSTOM", customHours: hours });
  };

  return (
    <View style={[styles.wrapper, { borderColor: theme.colors.outline }]}>
      <Pressable
        onPress={() => setExpanded((prev) => !prev)}
        style={styles.headerRow}
        accessibilityRole="button"
        accessibilityState={{ expanded }}
        accessibilityLabel={titleFor(scope)}
      >
        <View style={styles.headerText}>
          <Text style={[styles.title, { color: theme.colors.onSurface }]}>{titleFor(scope)}</Text>
          <Text style={[styles.summary, { color: theme.colors.onSurfaceVariant }]}>Currently: {summary}</Text>
        </View>
        {expanded ? (
          <ChevronUp size={20} color={theme.colors.onSurfaceVariant} />
        ) : (
          <ChevronDown size={20} color={theme.colors.onSurfaceVariant} />
        )}
      </Pressable>

      {expanded && (
        <View style={styles.body}>
          <Text style={[styles.description, { color: theme.colors.onSurfaceVariant }]}>{descriptionFor(scope)}</Text>

          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>How long should they stay?</Text>
          <View style={styles.chipRow}>
            {PRESET_OPTIONS.map((option) => {
              const selected = setting.duration === option;
              return (
                <Pressable
                  key={option}
                  onPress={() => handlePreset(option)}
                  disabled={isSaving}
                  style={[
                    styles.chip,
                    { backgroundColor: selected ? theme.colors.primary : theme.colors.surfaceVariant, opacity: isSaving ? 0.6 : 1 },
                  ]}
                  accessibilityRole="button"
                  accessibilityState={{ selected, disabled: isSaving }}
                  accessibilityLabel={`Move to Trash after ${AUTO_CLEAR_DURATION_LABELS[option]}`}
                >
                  <Text
                    style={[styles.chipText, { color: selected ? theme.colors.onPrimary : theme.colors.onSurfaceVariant }]}
                  >
                    {AUTO_CLEAR_DURATION_LABELS[option]}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          <View style={styles.customRow}>
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Automatically move to Trash after</Text>
            <View style={styles.customInputRow}>
              <TextInput
                value={customHoursText}
                onChangeText={setCustomHoursText}
                placeholder="7"
                keyboardType="decimal-pad"
                placeholderTextColor={theme.colors.onSurfaceVariant}
                style={[styles.customInput, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
                accessibilityLabel="Custom number of hours"
              />
              <Text style={[styles.customUnit, { color: theme.colors.onSurfaceVariant }]}>hours</Text>
              <Pressable
                onPress={handleSetCustom}
                disabled={isSaving}
                style={[styles.setButton, { backgroundColor: theme.colors.primary, opacity: isSaving ? 0.6 : 1 }]}
                accessibilityRole="button"
                accessibilityLabel="Set custom auto-clear duration"
              >
                <Text style={[styles.setButtonText, { color: theme.colors.onPrimary }]}>
                  {isSaving ? "Saving…" : "Set"}
                </Text>
              </Pressable>
            </View>
            {saveError && <Text style={[styles.error, { color: theme.colors.error }]}>{saveError}</Text>}
            {justSaved && !saveError && <Text style={[styles.success, { color: theme.colors.secondary }]}>Saved.</Text>}
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { borderWidth: 1, borderRadius: radius.md, overflow: "hidden" },
  headerRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm, padding: spacing.md, minHeight: 48 },
  headerText: { flex: 1, gap: 2 },
  title: { ...typography.body, fontWeight: "600" },
  summary: { ...typography.bodySmall },
  body: { paddingHorizontal: spacing.md, paddingBottom: spacing.md, gap: spacing.sm },
  description: { ...typography.bodySmall },
  label: { ...typography.bodySmall, fontWeight: "600" },
  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  chip: { paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: radius.pill, minHeight: 36, justifyContent: "center" },
  chipText: { ...typography.bodySmall, fontWeight: "600" },
  customRow: { gap: spacing.xs, marginTop: spacing.xs },
  customInputRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  customInput: { width: 64, borderWidth: 1, borderRadius: radius.sm, paddingHorizontal: spacing.sm, minHeight: 40, ...typography.body },
  customUnit: { ...typography.body },
  error: { ...typography.bodySmall },
  success: { ...typography.bodySmall, fontWeight: "600" },
  setButton: { marginLeft: "auto", minHeight: 36, paddingHorizontal: spacing.md, borderRadius: radius.pill, justifyContent: "center" },
  setButtonText: { ...typography.bodySmall, fontWeight: "700" },
});
