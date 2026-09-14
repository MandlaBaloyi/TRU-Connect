/**
 * InlineEditField -- one labelled profile row that reads as its
 * CURRENT VALUE with an explicit "Edit" control, and only becomes a
 * text input when Edit is tapped (then confirm / cancel).
 *
 * Replaces the old always-editable stack of paper TextInputs on the
 * supplier Profile screen, where it was unclear on-device which text
 * was a value you have vs. an input you can change. Each row saves
 * itself on confirm -- there's no screen-level Save button anymore.
 *
 * MOVED HERE FROM supplier/my-account/components WHEN THE BUSINESS
 * PROFILE NEEDED THE SAME ROW. Copying it would have produced two
 * definitions of "what an editable profile field looks like", which is
 * exactly the drift the supplier screen introduced this component to
 * end. It depends on nothing role-specific.
 *
 * The save call is the parent's (`onSave`) -- this component owns only
 * the view/edit toggle, the draft state, the in-flight spinner, and
 * surfacing a validation or save error inline without collapsing.
 */
import React, { useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
  type KeyboardTypeOptions,
} from "react-native";
import { TextInput, useTheme } from "react-native-paper";
import { Check, Lock, X } from "lucide-react-native";

import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  label: string;
  value: string | null;
  /** What READ mode shows, when it should differ from the editable
   *  value. Added for money: a minimum order edits as a plain number
   *  ("500", so the numeric keypad and validation stay simple) but must
   *  READ as currency ("R500.00") -- showing the raw number made it
   *  ambiguous whether it meant rands or cents. Falls back to `value`
   *  when omitted, so every existing caller is unaffected. */
  displayValue?: string | null;
  onSave: (next: string) => Promise<void>;
  placeholder?: string;
  /** Shown in read mode when the value is empty. */
  emptyText?: string;
  keyboardType?: KeyboardTypeOptions;
  autoCapitalize?: "none" | "sentences" | "words" | "characters";
  multiline?: boolean;
  maxLength?: number;
  /** Static hint shown under the field while editing. */
  helperText?: string;
  /** Return an error string to block the save, or null to allow it. */
  validate?: (next: string) => string | null;
  disabled?: boolean;
  /** Drop the bottom hairline — for the last row inside a grouped card. */
  noDivider?: boolean;
}

export function InlineEditField({
  label,
  value,
  displayValue,
  onSave,
  placeholder,
  emptyText = "Not set",
  keyboardType,
  autoCapitalize = "sentences",
  multiline = false,
  maxLength,
  helperText,
  validate,
  disabled = false,
  noDivider = false,
}: Props) {
  const theme = useTheme();
  const [editing, setEditing] = useState(false);
  // What read mode shows: displayValue when given (money reads as
  // "R500.00" while editing as "500"), otherwise the raw value.
  const shown = displayValue ?? value;
  const [draft, setDraft] = useState(value ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const beginEdit = () => {
    setDraft(value ?? "");
    setError(null);
    setEditing(true);
  };

  const cancel = () => {
    setEditing(false);
    setError(null);
    setDraft(value ?? "");
  };

  const confirm = async () => {
    const next = draft.trim();
    const validationError = validate?.(next) ?? null;
    if (validationError) {
      setError(validationError);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSave(next);
      setEditing(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't save. Try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <View
      style={[
        styles.wrap,
        { borderBottomColor: theme.colors.outlineVariant },
        noDivider && styles.noDivider,
      ]}
    >
      <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>{label}</Text>

      {editing ? (
        <>
          <View style={styles.editRow}>
            <TextInput
              mode="outlined"
              dense
              autoFocus
              value={draft}
              onChangeText={(t) => setDraft(maxLength ? t.slice(0, maxLength) : t)}
              placeholder={placeholder}
              keyboardType={keyboardType}
              autoCapitalize={autoCapitalize}
              multiline={multiline}
              style={styles.input}
              editable={!saving}
            />
            {saving ? (
              <ActivityIndicator style={styles.actionBtn} color={theme.colors.primary} />
            ) : (
              <>
                <Pressable onPress={confirm} style={styles.actionBtn} accessibilityRole="button" accessibilityLabel={`Save ${label}`}>
                  <Check size={20} color={theme.colors.primary} strokeWidth={2.4} />
                </Pressable>
                <Pressable onPress={cancel} style={styles.actionBtn} accessibilityRole="button" accessibilityLabel={`Cancel editing ${label}`}>
                  <X size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2.4} />
                </Pressable>
              </>
            )}
          </View>
          {maxLength && multiline ? (
            <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>
              {maxLength - draft.length} characters left
            </Text>
          ) : helperText ? (
            <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>{helperText}</Text>
          ) : null}
        </>
      ) : (
        <>
          <View style={styles.readRow}>
            <Text
              style={[
                styles.value,
                { color: shown ? theme.colors.onSurface : theme.colors.onSurfaceVariant },
              ]}
              numberOfLines={multiline ? 3 : 1}
            >
              {shown || emptyText}
            </Text>
            {disabled ? (
              <Lock size={15} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
            ) : (
              <Pressable onPress={beginEdit} hitSlop={8} accessibilityRole="button" accessibilityLabel={`Edit ${label}`}>
                <Text style={[styles.editLink, { color: theme.colors.primary }]}>Edit</Text>
              </Pressable>
            )}
          </View>
          {disabled && helperText && (
            <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>{helperText}</Text>
          )}
        </>
      )}

      {error && <Text style={[styles.error, { color: theme.colors.error }]}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { paddingVertical: spacing.sm, borderBottomWidth: StyleSheet.hairlineWidth, gap: spacing.xs },
  noDivider: { borderBottomWidth: 0 },
  label: { ...typography.caption, textTransform: "uppercase", letterSpacing: 0.5 },
  readRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: spacing.md },
  value: { ...typography.body, flex: 1 },
  editLink: { ...typography.bodySmall, fontWeight: "700" },
  editRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  input: { flex: 1, backgroundColor: "transparent" },
  actionBtn: { width: 36, height: 36, alignItems: "center", justifyContent: "center" },
  hint: { ...typography.caption },
  error: { ...typography.bodySmall },
});
