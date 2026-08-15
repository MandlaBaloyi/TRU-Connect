import React, { useState } from "react";
import { ScrollView, StyleSheet, Text } from "react-native";
import { TextInput, useTheme } from "react-native-paper";
import { CheckCircle2, UserPlus } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { Hero, Note } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import { ApiError } from "@/services/api/apiClient";

import { useInviteBusiness } from "../hooks/useInviteBusiness";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Mirrors business/find-supplier/screens/InviteSupplierScreen.tsx —
 * the reverse direction. Real, tested backend
 * (POST /supplier-discovery/business-invitations): same secure,
 * expiring, single-use ticket mechanism, same auto-created PENDING
 * relationship once the invited business registers and verifies.
 */
export default function InviteBusinessScreen() {
  const theme = useTheme();
  const { invite, isInviting, isSent, error, reset } = useInviteBusiness();
  const [email, setEmail] = useState("");

  const isValidEmail = EMAIL_PATTERN.test(email.trim());

  const handleInvite = async () => {
    try {
      await invite(email.trim());
    } catch {
      // Surfaced via `error` below — nothing further to do here.
    }
  };

  const handleInviteAnother = () => {
    setEmail("");
    reset();
  };

  if (isSent) {
    return (
      <ScreenContainer hasNativeHeader>
        <ScrollView contentContainerStyle={styles.content}>
          <Hero
            icon={<CheckCircle2 size={28} color={theme.colors.secondary} strokeWidth={1.8} />}
            title="Invite sent"
            description={`${email.trim()} will get an email with a link to join TruConnect.`}
          />
          <Note>
            Once they register and verify their email, they'll show up as a pending connection you can approve —
            the same way any business you find directly does.
          </Note>
          <PrimaryButton onPress={handleInviteAnother}>Invite another business</PrimaryButton>
        </ScrollView>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Hero
          icon={<UserPlus size={28} color={theme.colors.primary} strokeWidth={1.8} />}
          title="Invite a business"
          description="Invite a business who isn't on TruConnect yet. They'll get an email with a link to join."
        />
        <TextInput
          mode="outlined"
          label="Business's email address"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
          autoFocus
        />
        {error && (
          <Text style={[styles.error, { color: theme.colors.error }]}>
            {error instanceof ApiError ? error.message : "Couldn't send that invite. Try again."}
          </Text>
        )}
        <PrimaryButton onPress={handleInvite} loading={isInviting} disabled={!isValidEmail || isInviting}>
          Send invite
        </PrimaryButton>
        <Note>They'll be connected to you automatically once they register and verify their email.</Note>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingHorizontal: spacing.md, paddingBottom: spacing.xxl, gap: spacing.md },
  error: { ...typography.bodySmall },
});
