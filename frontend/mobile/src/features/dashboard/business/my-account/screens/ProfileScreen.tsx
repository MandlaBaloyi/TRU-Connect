import React, { useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { TextInput, useTheme } from "react-native-paper";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useBusinessProfileMutations } from "@/features/dashboard/business/business-profile/hooks/useBusinessProfileMutations";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useAccountProfile } from "../hooks/useAccountProfile";
import { useBio } from "../hooks/useBio";
import { useProfileImage } from "../hooks/useProfileImage";
import { useUpdateDisplayName } from "../hooks/useDisplayName";
import { useUpdateContactField } from "../hooks/useContactDetails";
import { ProfileAvatar } from "../components/ProfileAvatar";
import { BIO_MAX_LENGTH } from "../types";

/**
 * Profile — all identity fields editable INLINE on one screen, ONE
 * Save button, rather than each field navigating to its own separate
 * screen. Revised from the previous "hub with rows linking out"
 * version per direct feedback.
 *
 * Business name here is GENUINELY REAL, not mocked — it calls
 * business-profile's own already-real saveBusinessDetails mutation
 * directly (see useAccountProfile.ts's own precedent for reading from
 * that same domain read-only; this extends that to a write, the
 * natural next step of the same established pattern). Contact/bio/
 * name stay mock-backed, same as before — only the SAVE mechanism
 * changed, not what's real vs mock underneath each field.
 *
 * Each field only calls its own mutation if it actually changed —
 * avoids firing four mock requests when someone only touched the bio.
 */
export default function ProfileScreen() {
  const router = useRouter();
  const theme = useTheme();

  const { summary, isLoading, isError, refetch } = useAccountProfile();
  const { bio, save: saveBio } = useBio();
  const { profileImage } = useProfileImage();
  const updateDisplayName = useUpdateDisplayName();
  const updateContactField = useUpdateContactField();
  const { saveBusinessDetails } = useBusinessProfileMutations();

  const [firstName, setFirstName] = useState(summary?.firstName ?? "");
  const [lastName, setLastName] = useState(summary?.lastName ?? "");
  const [email, setEmail] = useState(summary?.email ?? "");
  const [phone, setPhone] = useState(summary?.phoneNumber ?? "");
  const [bioValue, setBioValue] = useState(bio ?? "");
  const [businessName, setBusinessName] = useState(summary?.businessName ?? "");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !summary) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load your profile. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const fullName = [firstName, lastName].filter(Boolean).join(" ") || summary.email;

  const handleSave = async () => {
    setError(null);
    setIsSaving(true);
    try {
      if (firstName.trim() !== (summary.firstName ?? "") || lastName.trim() !== (summary.lastName ?? "")) {
        await updateDisplayName.mutateAsync({ firstName, lastName });
      }
      if (email.trim() !== summary.email) {
        await updateContactField.mutateAsync({ field: "email", value: email });
      }
      if (phone.trim() !== (summary.phoneNumber ?? "")) {
        await updateContactField.mutateAsync({ field: "phone", value: phone });
      }
      if (bioValue.trim() !== (bio ?? "")) {
        await saveBio(bioValue);
      }
      if (businessName.trim() !== (summary.businessName ?? "") && businessName.trim().length > 0) {
        await saveBusinessDetails({ businessName: businessName.trim() });
      }
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't save your changes. Try again.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.avatarBlock}>
          <ProfileAvatar
            name={fullName}
            imageUri={profileImage?.status === "approved" ? profileImage.localUri : null}
            onPress={() => router.push("/business/my-account/profile-image" as any)}
            verified={summary.verification === "VERIFIED"}
          />
        </View>

        <View style={styles.row}>
          <TextInput
            mode="outlined"
            label="First name"
            value={firstName}
            onChangeText={setFirstName}
            style={styles.half}
          />
          <TextInput
            mode="outlined"
            label="Last name"
            value={lastName}
            onChangeText={setLastName}
            style={styles.half}
          />
        </View>

        <TextInput
          mode="outlined"
          label="Business name"
          value={businessName}
          onChangeText={setBusinessName}
        />

        <TextInput
          mode="outlined"
          label="Email address"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
        />

        <TextInput mode="outlined" label="Phone number" value={phone} onChangeText={setPhone} keyboardType="phone-pad" />

        <TextInput
          mode="outlined"
          label="Bio"
          value={bioValue}
          onChangeText={(text) => setBioValue(text.slice(0, BIO_MAX_LENGTH))}
          multiline
          numberOfLines={3}
        />
        <Text style={[styles.counter, { color: theme.colors.onSurfaceVariant }]}>
          {BIO_MAX_LENGTH - bioValue.length} characters left
        </Text>

        {error && <Text style={[styles.error, { color: theme.colors.error }]}>{error}</Text>}

        <PrimaryButton onPress={handleSave} loading={isSaving} disabled={isSaving}>
          Save
        </PrimaryButton>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingHorizontal: spacing.md, paddingBottom: spacing.xxl, gap: spacing.md },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  avatarBlock: { alignItems: "center", paddingBottom: spacing.sm },
  row: { flexDirection: "row", gap: spacing.sm },
  half: { flex: 1 },
  counter: { ...typography.bodySmall, textAlign: "right", marginTop: -spacing.sm },
  error: { ...typography.bodySmall },
});
