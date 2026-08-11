import React, { useEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Switch, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { useBusinessProfile, useBusinessProfileMutations } from "../hooks";
import type { ContactDetails } from "../types";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";

const EMPTY: ContactDetails = {
  usesSameAsAccountPhone: true,
  usesSameAsAccountEmail: true,
  whatsappSameAsPhone: true,
  whatsappNotUsed: false,
};

export default function ContactDetailsEditScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { profile, isLoading, isError, refetch } = useBusinessProfile();
  const { saveContactDetails, isSavingContactDetails } = useBusinessProfileMutations();

  const [draft, setDraft] = useState<ContactDetails>(EMPTY);
  const [initialised, setInitialised] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (profile && !initialised) {
      setDraft(profile.contactDetails);
      setInitialised(true);
    }
  }, [profile, initialised]);

  if (isLoading || !profile) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Could not load your contact details." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const handleSave = async () => {
    try {
      await saveContactDetails(draft);
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save. Try again.");
    }
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.toggleRow}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Use my personal number</Text>
          <Switch
            value={draft.usesSameAsAccountPhone}
            onValueChange={(usesSameAsAccountPhone) => setDraft({ ...draft, usesSameAsAccountPhone })}
          />
        </View>
        {!draft.usesSameAsAccountPhone && (
          <TextInput
            value={draft.phone ?? ""}
            onChangeText={(text) => setDraft({ ...draft, phone: text })}
            placeholder="Business phone number"
            placeholderTextColor={theme.colors.onSurfaceVariant}
            keyboardType="phone-pad"
            style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            accessibilityLabel="Business phone number"
          />
        )}

        <View style={styles.toggleRow}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Use my verified email</Text>
          <Switch
            value={draft.usesSameAsAccountEmail}
            onValueChange={(usesSameAsAccountEmail) => setDraft({ ...draft, usesSameAsAccountEmail })}
          />
        </View>
        {!draft.usesSameAsAccountEmail && (
          <TextInput
            value={draft.email ?? ""}
            onChangeText={(text) => setDraft({ ...draft, email: text })}
            placeholder="Business email address"
            placeholderTextColor={theme.colors.onSurfaceVariant}
            keyboardType="email-address"
            autoCapitalize="none"
            style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            accessibilityLabel="Business email address"
          />
        )}

        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>WhatsApp number</Text>
          <View style={styles.chipRow}>
            {[
              { key: "same", label: "Same as business phone" },
              { key: "different", label: "Different number" },
              { key: "none", label: "I don't use WhatsApp" },
            ].map((option) => {
              const selected =
                (option.key === "same" && draft.whatsappSameAsPhone && !draft.whatsappNotUsed) ||
                (option.key === "different" && !draft.whatsappSameAsPhone && !draft.whatsappNotUsed) ||
                (option.key === "none" && draft.whatsappNotUsed);
              return (
                <Pressable
                  key={option.key}
                  onPress={() =>
                    setDraft({ ...draft, whatsappSameAsPhone: option.key === "same", whatsappNotUsed: option.key === "none" })
                  }
                  style={[
                    styles.chip,
                    { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
                    selected && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
                  ]}
                  accessibilityRole="radio"
                  accessibilityState={{ selected }}
                >
                  <Text style={[styles.chipText, { color: selected ? theme.colors.onPrimary : theme.colors.onSurface }]}>
                    {option.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
          {!draft.whatsappSameAsPhone && !draft.whatsappNotUsed && (
            <TextInput
              value={draft.whatsapp ?? ""}
              onChangeText={(text) => setDraft({ ...draft, whatsapp: text })}
              placeholder="WhatsApp number"
              placeholderTextColor={theme.colors.onSurfaceVariant}
              keyboardType="phone-pad"
              style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface, marginTop: spacing.xs }]}
              accessibilityLabel="WhatsApp number"
            />
          )}
        </View>

        {error && <Text style={[styles.error, { color: theme.colors.error }]}>{error}</Text>}

        <PrimaryButton onPress={handleSave} loading={isSavingContactDetails} disabled={isSavingContactDetails}>
          Save
        </PrimaryButton>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.md },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  field: { gap: spacing.xs },
  label: { ...typography.bodySmall, fontWeight: "600" },
  toggleRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  input: { borderWidth: 1, borderRadius: 8, paddingHorizontal: spacing.md, minHeight: 48, ...typography.body },
  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  chip: { paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: 999, minHeight: 36, justifyContent: "center", borderWidth: 1 },
  chipText: { ...typography.bodySmall, fontWeight: "600" },
  error: { ...typography.bodySmall },
});
