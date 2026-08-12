import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { CreditCard, Mail, Phone, ShieldAlert, Trash2, UserX } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { Card, CardSection, StatusPill } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useAccountProfile } from "../hooks/useAccountProfile";
import { useBio } from "../hooks/useBio";
import { usePaymentMethods } from "../hooks/usePaymentMethods";
import { useProfileImage } from "../hooks/useProfileImage";
import { ProfileAvatar } from "../components/ProfileAvatar";
import { VerificationBadge } from "../components/VerificationBadge";

/**
 * My Account landing screen. Same progressive-disclosure principle as
 * Account Security's landing screen (see security/screens/
 * AccountSecurityScreen.tsx): shows STATE here, every control lives one
 * level down. Deliberately NOT a social-media profile (file.txt §1) —
 * no counts, no stats, no feed. Just: who is this, is it verified, how
 * do I reach it, how does it pay, how do I control it.
 */
export default function MyAccountScreen() {
  const router = useRouter();
  const theme = useTheme();

  const { summary, isLoading, isError, refetch } = useAccountProfile();
  const { bio } = useBio();
  const { paymentMethods } = usePaymentMethods();
  const { profileImage } = useProfileImage();

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
        <ErrorState message="Couldn't load your account. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const go = (path: string) => () => router.push(path as any);

  const fullName = [summary.firstName, summary.lastName].filter(Boolean).join(" ") || summary.email;
  const defaultMethod = paymentMethods.find((m) => m.isDefault);
  const accountStatusTone =
    summary.accountStatus === "active" ? "on" : summary.accountStatus === "suspended" ? "warning" : "off";
  const accountStatusLabel =
    summary.accountStatus === "active"
      ? "Active"
      : summary.accountStatus === "suspended"
        ? "Suspended"
        : summary.accountStatus === "deactivated"
          ? "Deactivated"
          : "Unknown";

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {/* Profile header */}
        <View style={styles.header}>
          <ProfileAvatar
            name={fullName}
            imageUri={profileImage?.status === "approved" ? profileImage.localUri : null}
            onPress={go("/business/my-account/profile-image")}
          />
          <Text style={[styles.name, { color: theme.colors.onSurface }]}>{fullName}</Text>
          {summary.businessName && (
            <Text style={[styles.businessName, { color: theme.colors.onSurfaceVariant }]}>
              {summary.businessName}
            </Text>
          )}
          <VerificationBadge status={summary.verification} />
          {bio && <Text style={[styles.bio, { color: theme.colors.onSurfaceVariant }]}>{bio}</Text>}
        </View>

        {/* Contact details */}
        <CardSection title="Contact details">
          <Card
            icon={(c) => <Phone size={20} color={c} />}
            label="Phone number"
            description={summary.phoneNumber ?? "Not set"}
            onPress={go("/business/my-account/edit-phone")}
          />
          <Card
            icon={(c) => <Mail size={20} color={c} />}
            label="Email address"
            description={summary.email}
            onPress={go("/business/my-account/edit-email")}
          />
        </CardSection>

        {/* About */}
        <CardSection title="About">
          <Card
            label="Bio"
            description={bio ?? "Tell customers a little about you"}
            onPress={go("/business/my-account/bio")}
          />
        </CardSection>

        {/* Payment methods */}
        <CardSection title="Payment methods">
          <Card
            icon={(c) => <CreditCard size={20} color={c} />}
            label="Payment methods"
            description={
              defaultMethod ? `Default: ${defaultMethod.displayLabel}` : `${paymentMethods.length} method(s)`
            }
            onPress={go("/business/my-account/payment-methods")}
          />
        </CardSection>

        {/* Account status */}
        <CardSection title="Account status">
          <Card
            label="Status"
            description="How TruConnect sees your account right now"
            status={<StatusPill label={accountStatusLabel} tone={accountStatusTone} />}
            onPress={go("/business/my-account/account-status")}
          />
        </CardSection>

        {/* Danger zone — visually separated per file.txt §4 */}
        <CardSection title="Danger zone">
          <Card
            tone="danger"
            icon={(c) => <UserX size={20} color={c} />}
            label="Temporarily deactivate account"
            description="Hide your account until you come back"
            onPress={go("/business/my-account/deactivate-account")}
          />
          <Card
            tone="danger"
            icon={(c) => <Trash2 size={20} color={c} />}
            label="Delete account"
            description="Permanently request account deletion"
            onPress={go("/business/my-account/delete-account")}
          />
        </CardSection>

        {summary.accountStatus === "suspended" && (
          <View style={[styles.suspendedNote, { backgroundColor: theme.colors.errorContainer }]}>
            <ShieldAlert size={18} color={theme.colors.error} />
            <Text style={[styles.suspendedText, { color: theme.colors.error }]}>
              Your account is suspended by TruConnect. Only TruConnect can lift a suspension.
            </Text>
          </View>
        )}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.xl },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  header: { alignItems: "center", gap: spacing.xs, paddingHorizontal: spacing.lg },
  name: { ...typography.h1, marginTop: spacing.sm },
  businessName: { ...typography.body },
  bio: { ...typography.bodySmall, textAlign: "center", marginTop: spacing.xs, lineHeight: 19 },
  suspendedNote: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    padding: spacing.md,
    borderRadius: 12,
    marginHorizontal: spacing.md,
  },
  suspendedText: { ...typography.bodySmall, flex: 1, lineHeight: 18 },
});
