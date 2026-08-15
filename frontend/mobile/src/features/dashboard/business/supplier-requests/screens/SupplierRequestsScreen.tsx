import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Users } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { EmptyState } from "@/components/feedback/EmptyState";
import { ErrorState } from "@/components/feedback/ErrorState";
import { spacing } from "@/theme/spacing";

import { useSupplierRequests } from "../hooks/useSupplierRequests";
import { SupplierRequestCard } from "../components/SupplierRequestCard";

/**
 * Supplier Requests — the reverse direction of Customer Requests
 * (supplier/customer-requests/screens/CustomerRequestsScreen.tsx),
 * mirrored exactly. The business's own "suppliers want to connect
 * with you" surface. Only PENDING requests show here.
 */
export default function SupplierRequestsScreen() {
  const router = useRouter();
  const theme = useTheme();
  const { requests, isLoading, isError, refetch } = useSupplierRequests();

  if (isLoading) {
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
        <ErrorState message="Couldn't load your requests. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  if (requests.length === 0) {
    return (
      <ScreenContainer hasNativeHeader>
        <EmptyState
          icon={<Users size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
          message="No pending requests. Suppliers that want to connect with you will show up here."
        />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.list} showsVerticalScrollIndicator={false}>
        {requests.map((request) => (
          <SupplierRequestCard
            key={request.id}
            request={request}
            onPress={() => router.push(`/business/supplier-requests/${request.id}` as any)}
          />
        ))}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  list: { padding: spacing.md, gap: spacing.sm },
});
