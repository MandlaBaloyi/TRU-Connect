import React, { useMemo, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Check, X } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SecurityNote } from "../components/SecurityUI";
import { changePassword } from "../services/securityService";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import { TextInput } from "react-native-paper";

interface Rule {
  label: string;
  test: (value: string) => boolean;
}

/** Requirements shown LIVE as the user types, rather than only failing
 *  on submit — the user should never have to guess what's wrong. */
const RULES: Rule[] = [
  { label: "At least 8 characters", test: (v) => v.length >= 8 },
  { label: "One uppercase letter", test: (v) => /[A-Z]/.test(v) },
  { label: "One lowercase letter", test: (v) => /[a-z]/.test(v) },
  { label: "One number", test: (v) => /\d/.test(v) },
];

export default function ChangePasswordScreen() {
  const router = useRouter();
  const theme = useTheme();

  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNext, setShowNext] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const ruleResults = useMemo(() => RULES.map((r) => ({ ...r, passed: r.test(next) })), [next]);
  const allRulesPass = ruleResults.every((r) => r.passed);
  const matches = next.length > 0 && next === confirm;
  const canSubmit = current.length > 0 && allRulesPass && matches && !isSaving;

  const handleSubmit = async () => {
    setError(null);
    // Checked here as well as via canSubmit so the reason is explicit
    // if the button is ever reachable in an invalid state.
    if (next === current) {
      setError("Your new password must be different from your current one.");
      return;
    }
    setIsSaving(true);
    try {
      await changePassword({ currentPassword: current, newPassword: next });
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not change your password. Try again.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
        <TextInput
          mode="outlined"
          label="Current password"
          value={current}
          onChangeText={setCurrent}
          secureTextEntry={!showCurrent}
          autoCapitalize="none"
          right={<TextInput.Icon icon={showCurrent ? "eye-off" : "eye"} onPress={() => setShowCurrent((s) => !s)} />}
        />

        <TextInput
          mode="outlined"
          label="New password"
          value={next}
          onChangeText={setNext}
          secureTextEntry={!showNext}
          autoCapitalize="none"
          right={<TextInput.Icon icon={showNext ? "eye-off" : "eye"} onPress={() => setShowNext((s) => !s)} />}
        />

        <View style={[styles.rules, { backgroundColor: theme.colors.surfaceVariant }]}>
          {ruleResults.map((rule) => (
            <View key={rule.label} style={styles.ruleRow}>
              {rule.passed ? (
                <Check size={16} color={theme.colors.secondary} strokeWidth={3} />
              ) : (
                <X size={16} color={theme.colors.onSurfaceVariant} strokeWidth={2.5} />
              )}
              <Text
                style={[
                  styles.ruleText,
                  { color: rule.passed ? theme.colors.onSurface : theme.colors.onSurfaceVariant },
                ]}
              >
                {rule.label}
              </Text>
            </View>
          ))}
        </View>

        <TextInput
          mode="outlined"
          label="Confirm new password"
          value={confirm}
          onChangeText={setConfirm}
          secureTextEntry={!showNext}
          autoCapitalize="none"
          error={confirm.length > 0 && !matches}
        />
        {confirm.length > 0 && !matches && (
          <Text style={[styles.error, { color: theme.colors.error }]}>Passwords don't match.</Text>
        )}

        {error && <Text style={[styles.error, { color: theme.colors.error }]}>{error}</Text>}

        <PrimaryButton onPress={handleSubmit} loading={isSaving} disabled={!canSubmit}>
          Change password
        </PrimaryButton>

        <SecurityNote>
          Changing your password signs you out everywhere else. You'll stay signed in on this device.
        </SecurityNote>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.md },
  rules: { padding: spacing.md, borderRadius: radius.md, gap: spacing.sm },
  ruleRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  ruleText: { ...typography.bodySmall },
  error: { ...typography.bodySmall },
});
