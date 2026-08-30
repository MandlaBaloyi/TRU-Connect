import React, { useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { TextInput, useTheme } from "react-native-paper";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SwitchCard } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useAccountProfile } from "../hooks/useAccountProfile";
import { useUpdateDisplayName } from "../hooks/useDisplayName";
import { useUpdateContactField } from "../hooks/useContactDetails";
import { useSupplierProfile } from "../hooks/useSupplierProfile";
import { useProfileImage } from "../hooks/useProfileImage";
import { ProfileAvatar } from "../components/ProfileAvatar";
import { BIO_MAX_LENGTH } from "../types";

/**
 * Profile — supplier side, mirrors business/my-account/screens/
 * ProfileScreen.tsx's own inline-editable-single-form redesign.
 *
 * Business name, bio (SupplierProfile.description), and the three
 * contact channels below are ALL GENUINELY REAL now, all through ONE
 * comprehensive PATCH /supplier-discovery/my-profile call -- the
 * first real write path this whole domain has ever had. category/
 * location/photoVisibility/visibleImageSource are passed straight
 * through unchanged on every save (read from the same profile this
 * screen already loaded) -- this screen was never meant to expose
 * those as editable (a real, deliberate earlier decision tied to a
 * future verification flow, see types.ts's own history), so every
 * save here must never silently reset them to their defaults.
 *
 * WHATSAPP/TIKTOK/CONTACT EMAIL ARE DELIBERATELY LABELLED "Business
 * contact" -- distinct from the "Email address" field above them,
 * which is the account's own LOGIN email (a completely different
 * field, different purpose). Getting these two confused would mean a
 * supplier accidentally sharing their login email with businesses, or
 * accidentally changing their login credentials trying to set up a
 * customer-facing contact.
 *
 * Photo upload is REAL — fileRepository.ts/useFileUpload.ts/
 * useProfileImage.ts/ProfileImageScreen.tsx were ported directly from
 * the business side (that infrastructure is genuinely role-agnostic;
 * confirmed before copying, not assumed) so supplier has the exact
 * same real camera/library picker + mock upload pipeline business
 * already had.
 */
export default function ProfileScreen() {
  const router = useRouter();
  const theme = useTheme();

  const { summary, isLoading, isError, refetch } = useAccountProfile();
  const { profile, isLoading: isProfileLoading, save: saveProfile } = useSupplierProfile();
  const { profileImage } = useProfileImage();
  const updateDisplayName = useUpdateDisplayName();
  const updateContactField = useUpdateContactField();

  const [firstName, setFirstName] = useState(summary?.firstName ?? "");
  const [lastName, setLastName] = useState(summary?.lastName ?? "");
  const [email, setEmail] = useState(summary?.email ?? "");
  const [phone, setPhone] = useState(summary?.phoneNumber ?? "");
  const [businessNameValue, setBusinessNameValue] = useState(profile?.businessName ?? "");
  const [bioValue, setBioValue] = useState(profile?.description ?? "");
  const [whatsappValue, setWhatsappValue] = useState(profile?.whatsappNumber ?? "");
  const [contactEmailValue, setContactEmailValue] = useState(profile?.contactEmail ?? "");
  const [tiktokValue, setTiktokValue] = useState(profile?.tiktokHandle ?? "");
  const [shareContactDetails, setShareContactDetails] = useState(profile?.shareContactDetails ?? false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (isLoading || isProfileLoading) {
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

      // ONE comprehensive save for everything SupplierProfile owns --
      // category/location/photoVisibility/visibleImageSource are
      // passed through UNCHANGED from whatever this screen already
      // loaded, never invented or defaulted here, so a save on THIS
      // screen can never silently reset a field this screen doesn't
      // even show.
      if (businessNameValue.trim().length === 0) {
        throw new Error("Enter your business name.");
      }
      await saveProfile({
        businessName: businessNameValue,
        category: profile?.category ?? null,
        location: profile?.location ?? null,
        description: bioValue.trim() || null,
        photoVisibility: profile?.photoVisibility ?? "connections",
        visibleImageSource: profile?.visibleImageSource ?? "none",
        whatsappNumber: whatsappValue.trim() || null,
        contactEmail: contactEmailValue.trim() || null,
        tiktokHandle: tiktokValue.trim() || null,
        shareContactDetails,
      });

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
            onPress={() => router.push("/supplier/my-account/profile-image" as any)}
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

        <TextInput mode="outlined" label="Business name" value={businessNameValue} onChangeText={setBusinessNameValue} />

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

        <Text style={[styles.sectionTitle, { color: theme.colors.onSurfaceVariant }]}>Business contact</Text>
        <Text style={[styles.sectionHint, { color: theme.colors.onSurfaceVariant }]}>
          Shown to businesses you're connected with, on the products they view from you -- separate from your account
          login email above.
        </Text>

        <TextInput
          mode="outlined"
          label="WhatsApp number (optional)"
          placeholder="e.g. 27821234567, including country code"
          value={whatsappValue}
          onChangeText={setWhatsappValue}
          keyboardType="phone-pad"
        />

        <TextInput
          mode="outlined"
          label="Business contact email (optional)"
          value={contactEmailValue}
          onChangeText={setContactEmailValue}
          keyboardType="email-address"
          autoCapitalize="none"
        />

        <TextInput
          mode="outlined"
          label="TikTok handle (optional)"
          placeholder="e.g. myshop"
          value={tiktokValue}
          onChangeText={setTiktokValue}
          autoCapitalize="none"
        />

        <SwitchCard
          label="Share with connected businesses"
          description="Only businesses you're actively connected with can see these -- never anyone just browsing."
          value={shareContactDetails}
          onValueChange={setShareContactDetails}
        />

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
  sectionTitle: { ...typography.bodySmall, fontWeight: "700", textTransform: "uppercase", letterSpacing: 0.5, marginTop: spacing.sm },
  sectionHint: { ...typography.bodySmall, marginTop: -spacing.sm },
  error: { ...typography.bodySmall },
});
