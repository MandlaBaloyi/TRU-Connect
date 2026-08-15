import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import { useLocalSearchParams } from "expo-router";
import { useTheme } from "react-native-paper";
import { Package } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { EmptyState } from "@/components/feedback/EmptyState";
import { ErrorState } from "@/components/feedback/ErrorState";
import { ListCard } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";

import { useSupplierProducts } from "../hooks/useSupplierProducts";

/**
 * The minimal Catalogue slice's own frontend home — real, tested
 * data (name only, matching backend Product's own deliberately lean
 * shape), reached from a supplier's profile. NOT the full Catalogue
 * feature: no images, no price, no add-to-stock action yet — this
 * screen exists so the redesigned search card's own promise ("tap
 * through to view products") is genuinely true, not a dead end.
 *
 * Viewable regardless of connection status, matching this session's
 * own architecture-review decision: browsing stays open, only
 * ordering is gated.
 */
export default function SupplierProductsScreen() {
  const { supplierId } = useLocalSearchParams<{ supplierId: string }>();
  const theme = useTheme();
  const { products, isLoading, isError, refetch } = useSupplierProducts(supplierId ?? "");

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
        <ErrorState message="Couldn't load this supplier's products. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  if (products.length === 0) {
    return (
      <ScreenContainer hasNativeHeader>
        <EmptyState
          icon={<Package size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
          message="This supplier hasn't listed any products yet."
        />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.list} showsVerticalScrollIndicator={false}>
        {products.map((product) => (
          <ListCard key={product.id} icon={(c) => <Package size={20} color={c} />} title={product.name} />
        ))}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  list: { padding: spacing.md, gap: spacing.sm },
});
