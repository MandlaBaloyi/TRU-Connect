import React from "react";
import { ActivityIndicator, Alert, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams } from "expo-router";
import { useTheme } from "react-native-paper";
import { Mail, MapPin, Phone, Store, UserCheck, UserX } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { Note, formatWhen } from "@/components/lists/CardListUI";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useSupplierRequestDetail, useRespondToRequest } from "../hooks/useRespondToRequest";

/**
 * Supplier profile preview + Approve/Decline — the reverse direction
 * of supplier/customer-requests/screens/CustomerRequestDetailScreen.tsx.
 * Approving sets the underlying ConnectionRequest to ACTIVE — same
 * row Find Business's "Request Connection" created as PENDING.
 *
 * COPY DIRECTION, worth being precise about: `request.businessName`
 * actually holds the SUPPLIER's display name here (see this feature's
 * own types.ts — SupplierRequestSummary/Detail deliberately reuse the
 * same field name as Customer Requests' shared shape, but for THIS
 * direction it names the other party, who is a supplier). Approving
 * means the BUSINESS (viewing this screen) can now order FROM that
 * supplier — the opposite direction from Customer Requests' own copy,
 * where a business orders from the supplier reading that screen.
 */
export default function SupplierRequestDetailScreen() {
  const { requestId } = useLocalSearchParams<{ requestId: string }>();
  const theme = useTheme();
  const { data: request, isLoading, isError, refetch } = useSupplierRequestDetail(requestId ?? "");
  const { approve, isApproving, decline, isDeclining } = useRespondToRequest(requestId ?? "");

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !request) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load this request. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const confirmDecline = () => {
    Alert.alert("Decline this request?", `You won't be able to order from ${request.businessName}.`, [
      { text: "Cancel", style: "cancel" },
      { text: "Decline", style: "destructive", onPress: () => decline() },
    ]);
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <View style={[styles.iconWrap, { backgroundColor: theme.colors.primaryContainer }]}>
            <Store size={32} color={theme.colors.primary} strokeWidth={1.8} />
          </View>
          <Text style={[styles.name, { color: theme.colors.onSurface }]}>{request.businessName}</Text>
          {request.ownerName && (
            <Text style={[styles.owner, { color: theme.colors.onSurfaceVariant }]}>{request.ownerName}</Text>
          )}
        </View>

        <View style={styles.metaBlock}>
          {request.category && (
            <View style={styles.metaRow}>
              <Store size={16} color={theme.colors.onSurfaceVariant} />
              <Text style={[styles.metaText, { color: theme.colors.onSurfaceVariant }]}>{request.category}</Text>
            </View>
          )}
          {request.location && (
            <View style={styles.metaRow}>
              <MapPin size={16} color={theme.colors.onSurfaceVariant} />
              <Text style={[styles.metaText, { color: theme.colors.onSurfaceVariant }]}>{request.location}</Text>
            </View>
          )}
          {request.maskedPhone && (
            <View style={styles.metaRow}>
              <Phone size={16} color={theme.colors.onSurfaceVariant} />
              <Text style={[styles.metaText, { color: theme.colors.onSurfaceVariant }]}>{request.maskedPhone}</Text>
            </View>
          )}
          {request.maskedEmail && (
            <View style={styles.metaRow}>
              <Mail size={16} color={theme.colors.onSurfaceVariant} />
              <Text style={[styles.metaText, { color: theme.colors.onSurfaceVariant }]}>{request.maskedEmail}</Text>
            </View>
          )}
        </View>

        <Text style={[styles.requestedAt, { color: theme.colors.onSurfaceVariant }]}>
          Requested {formatWhen(request.requestedAt)}
        </Text>

        {request.status === "PENDING" && (
          <View style={styles.actions}>
            <PrimaryButton onPress={() => approve()} loading={isApproving} disabled={isApproving || isDeclining}>
              Approve
            </PrimaryButton>
            <PrimaryButton
              onPress={confirmDecline}
              loading={isDeclining}
              disabled={isApproving || isDeclining}
              buttonColor={theme.colors.errorContainer}
              textColor={theme.colors.error}
            >
              Decline
            </PrimaryButton>
          </View>
        )}

        {request.status === "ACTIVE" && (
          <View style={[styles.statusBanner, { backgroundColor: theme.colors.secondaryContainer }]}>
            <UserCheck size={16} color={theme.colors.secondary} />
            <Text style={[styles.statusBannerText, { color: theme.colors.secondary }]}>
              Approved — you can now order from {request.businessName}.
            </Text>
          </View>
        )}

        {request.status === "DECLINED" && (
          <View style={[styles.statusBanner, { backgroundColor: theme.colors.surfaceVariant }]}>
            <UserX size={16} color={theme.colors.onSurfaceVariant} />
            <Text style={[styles.statusBannerText, { color: theme.colors.onSurfaceVariant }]}>Declined.</Text>
          </View>
        )}

        <Note>Approving lets you place stock orders with {request.businessName} once ordering is available.</Note>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingHorizontal: spacing.md, paddingBottom: spacing.xxl, gap: spacing.lg },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  header: { alignItems: "center", gap: spacing.xs },
  iconWrap: { width: 72, height: 72, borderRadius: 36, alignItems: "center", justifyContent: "center" },
  name: { ...typography.h1, textAlign: "center" },
  owner: { ...typography.body },
  metaBlock: { gap: spacing.xs },
  metaRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  metaText: { ...typography.body },
  requestedAt: { ...typography.bodySmall, textAlign: "center" },
  actions: { gap: spacing.sm },
  statusBanner: { flexDirection: "row", alignItems: "center", gap: spacing.xs, borderRadius: radius.lg, padding: spacing.md },
  statusBannerText: { ...typography.bodySmall, fontWeight: "600", flex: 1 },
});
