/**
 * BusinessProfileScreen — "My Business". Thin orchestration only.
 *
 * LAYOUT: native header (from _layout.tsx) -> guided/settled banner +
 * completion bar (fixed, does not scroll) -> the Contact/Business/
 * Verification tab bar (also fixed) -> tab-specific content
 * (scrollable). The tab bar being fixed matters: it should always be
 * reachable without scrolling back up, since switching tabs is the
 * primary way to move around this screen now that there's no
 * accordion collapse to fall back on.
 *
 * Each tab shows plain ProfileCards (no collapse/expand — the tabs
 * already provide the focus an accordion used to), each with its own
 * EditButton navigating to that section's dedicated edit screen.
 */

import React, { useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import { useTheme } from "react-native-paper";

import { useBusinessProfile } from "../hooks";
import { CompletionBar, ProfileCard, ProfileTabBar, VerificationChecklist } from "../components";
import type { ProfileTab } from "../components";
import {
  BusinessDetailsSection,
  ContactDetailsSection,
  LocationSection,
  OperatingHistorySection,
  SupplierInfoSection,
  TradingDetailsSection,
} from "../components/sections";
import { spacing } from "@/theme/spacing";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";

export default function BusinessProfileScreen() {
  const theme = useTheme();
  const { profile, completion, isLoading, isError, refetch } = useBusinessProfile();
  const [tab, setTab] = useState<ProfileTab>("BUSINESS");

  if (isLoading) {
    return (
      <ScreenContainer>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !profile || !completion) {
    return (
      <ScreenContainer>
        <ErrorState message="Could not load your business profile." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer>
      <View style={styles.fixedHeader}>
        <CompletionBar percent={completion.overallPercent} />
      </View>

      <ProfileTabBar active={tab} onChange={setTab} />

      <ScrollView contentContainerStyle={styles.content}>
        {tab === "CONTACT" && (
          <ProfileCard title="Contact details" isComplete={completion.sections.contactDetails.isComplete}>
            <ContactDetailsSection contact={profile.contactDetails} />
          </ProfileCard>
        )}

        {tab === "BUSINESS" && (
          <>
            <ProfileCard title="Business details" isComplete={completion.sections.businessDetails.isComplete}>
              <BusinessDetailsSection details={profile.businessDetails} />
            </ProfileCard>
            <View style={[styles.divider, { backgroundColor: theme.colors.outline }]} />
            <ProfileCard title="Location" isComplete={completion.sections.location.isComplete}>
              <LocationSection location={profile.location} operatingModel={profile.businessDetails.operatingModel} />
            </ProfileCard>
            <View style={[styles.divider, { backgroundColor: theme.colors.outline }]} />
            <ProfileCard title="Trading details" isComplete={completion.sections.tradingDetails.isComplete}>
              <TradingDetailsSection trading={profile.tradingDetails} />
            </ProfileCard>
            <View style={[styles.divider, { backgroundColor: theme.colors.outline }]} />
            <ProfileCard title="Operating history" isComplete={completion.sections.operatingHistory.isComplete}>
              <OperatingHistorySection history={profile.operatingHistory} />
            </ProfileCard>
            <View style={[styles.divider, { backgroundColor: theme.colors.outline }]} />
            <ProfileCard title="Suppliers">
              <SupplierInfoSection supplierInfo={profile.supplierInfo} />
            </ProfileCard>
          </>
        )}

        {tab === "VERIFICATION" && (
          <ProfileCard title="Verification">
            <VerificationChecklist verification={profile.verification} />
          </ProfileCard>
        )}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  fixedHeader: { padding: spacing.md, paddingBottom: spacing.sm, gap: spacing.sm },
  content: { padding: spacing.md, paddingTop: spacing.md, paddingBottom: spacing.xxl, gap: spacing.md },
  divider: { height: StyleSheet.hairlineWidth, marginVertical: spacing.xs },
});
