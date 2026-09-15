import React from "react";
import { ActivityIndicator, FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { ChevronRight } from "lucide-react-native";

import { EntityAvatar } from "@/components/ui/EntityAvatar";
import { SupplierName } from "@/components/ui/SupplierName";
import { ErrorState } from "@/components/feedback/ErrorState";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { supplierProfileHref } from "../../../routes";
import { supplierMetaLine } from "../../components/cards/supplierMeta";
import { KindChipRow } from "../components/KindChipRow";
import { useExplore } from "../hooks/useExplore";
import { labelForKind } from "../services/exploreService";

/**
 * Explore — suppliers by what they ARE.
 *
 * THE BACKEND FOR THIS SHIPPED WITH NO SCREEN. Service, routes, the
 * chip builder and the name-collision guard were all built and
 * committed; nothing in the app could reach any of it. This is that
 * screen.
 *
 * THE FILTER IS A STATED FACT, NEVER A NAME MATCH, and that is the
 * point Mandla raised before the backend was written: "if a user
 * decides to name their supplier business wholesales, our explore must
 * not break". It reads supplier_kind, which somebody declared, so
 * "Seshego Cash & Carry" is found and a retailer trading as "Wholesale
 * Beauty Supplies" is not.
 *
 * A LIST, NOT A GRID, same as the feed's supplier screens: these are
 * entities to choose between, not goods to compare.
 *
 * IT DOES NOT REUSE FeedSupplierList, and the reason is the meta line.
 * That component prints DISTANCE, because every screen it serves is
 * ranked by distance and printing what you sorted by is the rule.
 * Nothing here is distance-ranked -- this list is ordered by having
 * stock, then tier, then the alphabet -- so showing a distance would
 * invite the reader to check an order that was never about distance.
 * What each row shows instead is what a supplier can do for you:
 * delivery, minimum order, how many businesses already buy from them.
 */
export default function ExploreScreen() {
  const router = useRouter();
  const theme = useTheme();
  const explore = useExplore();

  if (explore.isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (explore.isError) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState
          message="Couldn't load suppliers. Check your connection and try again."
          onRetry={explore.refetch}
        />
      </ScreenContainer>
    );
  }

  const activeLabel = labelForKind(explore.kind ?? "WHOLESALER").toLowerCase();

  return (
    <ScreenContainer hasNativeHeader paddingHorizontal={0}>
      {explore.kinds.length > 1 && (
        <KindChipRow kinds={explore.kinds} selected={explore.kind} onSelect={explore.setKind} />
      )}

      {explore.suppliers.length === 0 ? (
        <View style={styles.centre}>
          <Text style={[styles.emptyTitle, { color: theme.colors.onSurface }]}>
            No {activeLabel} yet
          </Text>
          <Text style={[styles.emptyBody, { color: theme.colors.onSurfaceVariant }]}>
            {/* NAMES THE REAL REASON. A supplier is missing from here
                because they are unverified or have no stock listed --
                not because anything failed -- and saying so is more
                useful than "nothing found". */}
            Suppliers appear here once they're verified and have stock listed. Invite one you
            already buy from and they'll show up.
          </Text>
        </View>
      ) : (
        <FlatList
          data={explore.suppliers}
          keyExtractor={(supplier) => supplier.id}
          contentContainerStyle={styles.content}
          ItemSeparatorComponent={() => (
            <View style={[styles.separator, { backgroundColor: theme.colors.outlineVariant }]} />
          )}
          ListHeaderComponent={
            <Text style={[styles.count, { color: theme.colors.onSurfaceVariant }]}>
              {explore.total} {explore.total === 1 ? "supplier" : "suppliers"}
            </Text>
          }
          renderItem={({ item }) => (
            <Pressable
              onPress={() => router.push(supplierProfileHref(item.id, item.businessName) as any)}
              style={({ pressed }) => [styles.row, { opacity: pressed ? 0.85 : 1 }]}
              accessibilityRole="button"
              accessibilityLabel={`${item.businessName}. ${supplierMetaLine(item)}`}
            >
              <EntityAvatar name={item.businessName} photoUrl={item.businessImageUrl} size={44} />
              <View style={styles.rowText}>
                <SupplierName
                  name={item.businessName}
                  verificationStatus={item.verificationStatus}
                  style={[styles.name, { color: theme.colors.onSurface }]}
                />
                <Text
                  style={[styles.meta, { color: theme.colors.onSurfaceVariant }]}
                  numberOfLines={1}
                >
                  {supplierMetaLine(item) || item.location || ""}
                </Text>
              </View>
              <ChevronRight size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
            </Pressable>
          )}
          refreshControl={
            <RefreshControl
              refreshing={explore.isRefetching}
              onRefresh={explore.refetch}
              tintColor={theme.colors.primary}
            />
          }
          showsVerticalScrollIndicator={false}
        />
      )}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.sm },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
  },
  rowText: { flex: 1, gap: 2 },
  name: { ...typography.body, fontWeight: "700" },
  meta: { ...typography.caption },
  separator: { height: StyleSheet.hairlineWidth, marginLeft: spacing.md + 44 + spacing.md },
  centre: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.xl,
    gap: spacing.sm,
  },
  emptyTitle: { ...typography.h2, textAlign: "center" },
  emptyBody: { ...typography.bodySmall, textAlign: "center" },
  count: { ...typography.caption, paddingHorizontal: spacing.md, paddingBottom: spacing.sm },
});
