/**
 * One shared form for editing a single contact field — used by both
 * EditPhoneScreen and EditEmailScreen so the two don't duplicate the
 * same 20 lines slightly differently (the exact class of thing the
 * three-header bug taught this project to avoid — see
 * TRU_CONNECT_HANDOFF.md §3).
 */
import React, { useState } from "react";
import { StyleSheet, Text } from "react-native";
import { TextInput, useTheme } from "react-native-paper";

import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  label: string;
  initialValue: string;
  keyboardType?: "phone-pad" | "email-address" | "default";
  autoCapitalize?: "none" | "sentences";
  onSave: (value: string) => Promise<void>;
}

export function ContactFieldForm({ label, initialValue, keyboardType = "default", autoCapitalize = "none", onSave }: Props) {
  const theme = useTheme();
  const [value, setValue] = useState(initialValue);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const canSubmit = value.trim().length > 0 && value.trim() !== initialValue && !isSaving;

  const handleSubmit = async () => {
    setError(null);
    setIsSaving(true);
    try {
      await onSave(value);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't save that. Try again.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <>
      <TextInput
        mode="outlined"
        label={label}
        value={value}
        onChangeText={setValue}
        keyboardType={keyboardType}
        autoCapitalize={autoCapitalize}
        autoFocus
      />
      {error && <Text style={[styles.error, { color: theme.colors.error }]}>{error}</Text>}
      <PrimaryButton onPress={handleSubmit} loading={isSaving} disabled={!canSubmit} style={styles.button}>
        Save
      </PrimaryButton>
    </>
  );
}

const styles = StyleSheet.create({
  error: { ...typography.bodySmall, marginTop: spacing.xs },
  button: { marginTop: spacing.md },
});
