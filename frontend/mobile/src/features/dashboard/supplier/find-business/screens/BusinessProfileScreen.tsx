import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams } from "expo-router";
import { useTheme } from "react-native-paper";
import { CalendarDays, MapPin, Store } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { Note } from "@/components/lists/CardListUI";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useBusinessProfile, useRequestConnection } from "../hooks/useConnectionRequest";

/**
 * Mirrors business/find-supplier/screens/SupplierProfileScreen.tsx —
 * no verification pill here, since BusinessProfilePreview has no such
 * field (BusinessProfile's real serialization doesn't return one, see
 * this feature's own types.ts).
 */
export default function BusinessProfileScreen() {
  const { businessId } = useLocalSearchParams<{ businessId: string }>();
  const theme = useTheme();
  const { data: business, isLoading, isError, refetch } = useBusinessProfile(businessId ?? "");
  const requestConnection = useRequestConnection(businessId ?? "");

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !business) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load this business. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const connectionStatus = business.connectionStatus;

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <View style={[styles.iconWrap, { backgroundColor: theme.colors.primaryContainer }]}>
            <Store size={32} color={theme.colors.primary} strokeWidth={1.8} />
          </View>
          <Text style={[styles.name, { color: theme.colors.onSurface }]}>{business.businessName}</Text>
        </View>

        <View style={styles.metaBlock}>
          {business.category && (
            <View style={styles.metaRow}>
              <Store size={16} color={theme.colors.onSurfaceVariant} />
              <Text style={[styles.metaText, { color: theme.colors.onSurfaceVariant }]}>{business.category}</Text>
            </View>
          )}
          {business.location && (
            <View style={styles.metaRow}>
              <MapPin size={16} color={theme.colors.onSurfaceVariant} />
              <Text style={[styles.metaText, { color: theme.colors.onSurfaceVariant }]}>{business.location}</Text>
            </View>
          )}
          {business.memberSinceYear && (
            <View style={styles.metaRow}>
              <CalendarDays size={16} color={theme.colors.onSurfaceVariant} />
              <Text style={[styles.metaText, { color: theme.colors.onSurfaceVariant }]}>
                On TruConnect since {business.memberSinceYear}
              </Text>
            </View>
          )}
        </View>

        {business.description && (
          <Text style={[styles.description, { color: theme.colors.onSurface }]}>{business.description}</Text>
        )}

        <ConnectionAction
          status={connectionStatus}
          onRequest={() => requestConnection.mutate()}
          isSubmitting={requestConnection.isPending}
        />

        <Note>
          Requesting a connection lets {business.businessName} know you'd like to supply them. They'll need to
          approve the request before orders can happen.
        </Note>
      </ScrollView>
    </ScreenContainer>
  );
}

function ConnectionAction({
  status,
  onRequest,
  isSubmitting,
}: {
  status: string;
  onRequest: () => void;
  isSubmitting: boolean;
}) {
  const theme = useTheme();

  if (status === "ACTIVE") {
    return (
      <View style={[styles.statusBanner, { backgroundColor: theme.colors.secondaryContainer }]}>
        <Text style={[styles.statusBannerText, { color: theme.colors.secondary }]}>
          You're connected — this business can place stock orders with you.
        </Text>
      </View>
    );
  }

  if (status === "PENDING") {
    return (
      <View style={[styles.statusBanner, { backgroundColor: theme.colors.surfaceVariant }]}>
        <Text style={[styles.statusBannerText, { color: theme.colors.onSurfaceVariant }]}>
          Connection request sent — waiting for the business to approve it.
        </Text>
      </View>
    );
  }

  if (status === "DECLINED") {
    return (
      <View style={[styles.statusBanner, { backgroundColor: theme.colors.errorContainer }]}>
        <Text style={[styles.statusBannerText, { color: theme.colors.error }]}>
          This business declined your connection request.
        </Text>
      </View>
    );
  }

  return (
    <PrimaryButton onPress={onRequest} loading={isSubmitting} disabled={isSubmitting}>
      Request Connection
    </PrimaryButton>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingHorizontal: spacing.md, paddingBottom: spacing.xxl, gap: spacing.lg },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  header: { alignItems: "center", gap: spacing.sm },
  iconWrap: { width: 72, height: 72, borderRadius: 36, alignItems: "center", justifyContent: "center" },
  name: { ...typography.h1, textAlign: "center" },
  metaBlock: { gap: spacing.xs },
  metaRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  metaText: { ...typography.body },
  description: { ...typography.body, lineHeight: 21 },
  statusBanner: { borderRadius: radius.lg, padding: spacing.md },
  statusBannerText: { ...typography.bodySmall, fontWeight: "600", textAlign: "center" },
});
