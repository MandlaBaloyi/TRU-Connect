import React from "react";
import { ActivityIndicator, Image, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { CalendarDays, ChevronRight, MapPin, Package, Store } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { Note, StatusPill } from "@/components/lists/CardListUI";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useSupplierProfile, useRequestConnection } from "../hooks/useConnectionRequest";

const VERIFICATION_TONE = { verified: "on", pending: "warning", unverified: "off" } as const;
const VERIFICATION_LABEL = { verified: "Verified", pending: "Pending", unverified: "Unverified" } as const;

/**
 * file.txt Phase 1/2 boundary: this is still the narrow discovery
 * preview (file.txt §4), not the supplier's full relationship-gated
 * profile — that richer view is what unlocks once
 * connectionStatus === "ACTIVE" (Phase 3, not built yet). Request
 * Connection here only ever produces PENDING in this mock — approval
 * itself is Phase 3, someone else's screen, not this one.
 */
export default function SupplierProfileScreen() {
  const { supplierId } = useLocalSearchParams<{ supplierId: string }>();
  const router = useRouter();
  const theme = useTheme();
  const { data: supplier, isLoading, isError, refetch } = useSupplierProfile(supplierId ?? "");
  const requestConnection = useRequestConnection(supplierId ?? "");

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !supplier) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load this supplier. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const connectionStatus = supplier.connectionStatus;

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          {supplier.photoUrl ? (
            <Image source={{ uri: supplier.photoUrl }} style={styles.photo} />
          ) : (
            <View style={[styles.iconWrap, { backgroundColor: theme.colors.primaryContainer }]}>
              <Store size={32} color={theme.colors.primary} strokeWidth={1.8} />
            </View>
          )}
          <Text style={[styles.name, { color: theme.colors.onSurface }]}>{supplier.businessName}</Text>
          <StatusPill
            label={VERIFICATION_LABEL[supplier.verificationStatus]}
            tone={VERIFICATION_TONE[supplier.verificationStatus]}
          />
        </View>

        <View style={styles.metaBlock}>
          {supplier.category && (
            <View style={styles.metaRow}>
              <Store size={16} color={theme.colors.onSurfaceVariant} />
              <Text style={[styles.metaText, { color: theme.colors.onSurfaceVariant }]}>{supplier.category}</Text>
            </View>
          )}
          {supplier.location && (
            <View style={styles.metaRow}>
              <MapPin size={16} color={theme.colors.onSurfaceVariant} />
              <Text style={[styles.metaText, { color: theme.colors.onSurfaceVariant }]}>{supplier.location}</Text>
            </View>
          )}
          {supplier.memberSinceYear && (
            <View style={styles.metaRow}>
              <CalendarDays size={16} color={theme.colors.onSurfaceVariant} />
              <Text style={[styles.metaText, { color: theme.colors.onSurfaceVariant }]}>
                On TruConnect since {supplier.memberSinceYear}
              </Text>
            </View>
          )}
        </View>

        {supplier.description && (
          <Text style={[styles.description, { color: theme.colors.onSurface }]}>{supplier.description}</Text>
        )}

        <Pressable
          onPress={() => router.push(`/business/find-supplier/products/${supplierId}` as any)}
          style={[styles.productsRow, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}
          accessibilityRole="button"
          accessibilityLabel="View products"
        >
          <Package size={20} color={theme.colors.primary} />
          <View style={styles.productsRowBody}>
            <Text style={[styles.productsRowTitle, { color: theme.colors.onSurface }]}>View Products</Text>
            <Text style={[styles.productsRowMeta, { color: theme.colors.onSurfaceVariant }]}>
              {supplier.productCount} product{supplier.productCount === 1 ? "" : "s"} listed
            </Text>
          </View>
          <ChevronRight size={18} color={theme.colors.onSurfaceVariant} />
        </Pressable>

        <ConnectionAction
          status={connectionStatus}
          onRequest={() => requestConnection.mutate()}
          isSubmitting={requestConnection.isPending}
        />

        <Note>
          Requesting a connection lets {supplier.businessName} know you'd like to order from them. They'll need to
          approve the request before you can place a stock order.
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
          You're connected — you can place stock orders with this supplier.
        </Text>
      </View>
    );
  }

  if (status === "PENDING") {
    return (
      <View style={[styles.statusBanner, { backgroundColor: theme.colors.surfaceVariant }]}>
        <Text style={[styles.statusBannerText, { color: theme.colors.onSurfaceVariant }]}>
          Connection request sent — waiting for the supplier to approve it.
        </Text>
      </View>
    );
  }

  if (status === "DECLINED") {
    return (
      <View style={[styles.statusBanner, { backgroundColor: theme.colors.errorContainer }]}>
        <Text style={[styles.statusBannerText, { color: theme.colors.error }]}>
          This supplier declined your connection request.
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
  photo: { width: 72, height: 72, borderRadius: 36 },
  name: { ...typography.h1, textAlign: "center" },
  metaBlock: { gap: spacing.xs },
  metaRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  metaText: { ...typography.body },
  description: { ...typography.body, lineHeight: 21 },
  productsRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    padding: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
  },
  productsRowBody: { flex: 1, gap: 2 },
  productsRowTitle: { ...typography.body, fontWeight: "700" },
  productsRowMeta: { ...typography.bodySmall },
  statusBanner: { borderRadius: radius.lg, padding: spacing.md },
  statusBannerText: { ...typography.bodySmall, fontWeight: "600", textAlign: "center" },
});
