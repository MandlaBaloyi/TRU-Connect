import React from "react";
import { Alert, ScrollView, StyleSheet, Text } from "react-native";
import { useTheme } from "react-native-paper";
import { UserX } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { Hero, Note } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useDeactivationRequest } from "../hooks/useAccountLifecycle";

/**
 * file.txt §4/§17: explain what deactivation means, what stays stored,
 * how reactivation works — WITHOUT claiming reactivation is actually
 * implemented, because it isn't (there's no backend endpoint for any
 * of this yet — see accountService.ts's docstring). Submitting here
 * never touches the real accountStatus that the rest of this feature
 * reads from useCurrentUser.
 */
export default function DeactivateAccountScreen() {
  const theme = useTheme();
  const { status, submit, isSubmitting } = useDeactivationRequest();

  if (status === "SUBMITTED") {
    return (
      <ScreenContainer hasNativeHeader>
        <ScrollView contentContainerStyle={styles.content}>
          <Hero
            icon={<UserX size={28} color={theme.colors.primary} strokeWidth={1.8} />}
            title="Request recorded"
            description="Your deactivation request has been noted in this session."
          />
          <Note>
            This isn't connected to a live backend yet, so nothing has actually changed on your account. When
            deactivation is fully built, submitting this request will genuinely take effect.
          </Note>
        </ScrollView>
      </ScreenContainer>
    );
  }

  const confirmAndSubmit = () => {
    Alert.alert(
      "Deactivate your account?",
      "Your account will be hidden until you sign back in. Your data stays stored and isn't deleted.",
      [
        { text: "Cancel", style: "cancel" },
        { text: "Deactivate", style: "destructive", onPress: () => submit() },
      ]
    );
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <Hero
          icon={<UserX size={28} color={theme.colors.error} strokeWidth={1.8} />}
          title="Temporarily deactivate account"
          description="Hide your account and pause activity until you decide to come back."
        />

        <Text style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>What this means</Text>
        <Text style={[styles.body, { color: theme.colors.onSurfaceVariant }]}>
          Your profile becomes hidden to other TruConnect users. Your data — Loan Book, Order Book, and business
          information — stays stored and is not deleted.
        </Text>

        <Text style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>How reactivation will work</Text>
        <Text style={[styles.body, { color: theme.colors.onSurfaceVariant }]}>
          Signing back in is expected to reactivate your account automatically once this is fully built.
        </Text>

        <Note>Deactivating isn't the same as deleting — nothing about your data is removed.</Note>

        <PrimaryButton onPress={confirmAndSubmit} loading={isSubmitting} buttonColor={theme.colors.error}>
          Deactivate my account
        </PrimaryButton>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.sm },
  sectionTitle: { ...typography.h2, marginTop: spacing.sm },
  body: { ...typography.body, lineHeight: 21 },
});
