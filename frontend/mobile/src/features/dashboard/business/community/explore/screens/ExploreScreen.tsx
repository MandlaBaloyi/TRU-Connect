import React from "react";
import { ActivityIndicator, FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { ChevronRight } from "lucide-react-native";

import { EntityAvatar } from "@/components/ui/EntityAvatar";
import { SupplierName } from "@/components/ui/SupplierName";
import { ErrorState } from "@/components/feedback/ErrorState";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { BrowseHeader } from "@/features/dashboard/business/browse/components/BrowseHeader";
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

  // WHICH KIND TO OPEN ON, when something sent us here already
  // knowing -- the feed's EXPLORE_KINDS section at the bottom of
  // Community. Absent when the overflow menu opened this screen cold,
  // and then useExplore falls back to the server's own default.
  //
  // IT SEEDS, IT DOES NOT CONTROL. The chip row must still be able to
  // change the kind afterwards, so this is an INITIAL value rather
  // than a prop threaded into the query -- otherwise the first tap of
  // a chip would fight the URL and lose.
  const { kind } = useLocalSearchParams<{ kind?: string }>();
  const explore = useExplore(typeof kind === "string" ? kind : undefined);
  const [search, setSearch] = React.useState("");

  // FILTERED IN THE APP, NOT THE SERVER, and only here. Explore
  // returns at most PAGE_SIZE = 40 suppliers of one kind and says
  // so in useExplore's own docstring -- "a market with more than
  // forty wholesalers of one kind is a problem this app does not
  // have yet". Filtering forty names in memory is honest; adding a
  // search parameter to an endpoint that never paginates would be
  // machinery with nothing to carry.
  const visible = React.useMemo(() => {
    const needle = search.trim().toLowerCase();
    if (!needle) return explore.suppliers;
    return explore.suppliers.filter((s) =>
      (s.businessName ?? "").toLowerCase().includes(needle)
    );
  }, [explore.suppliers, search]);

  const activeLabel = labelForKind(explore.kind ?? "WHOLESALER").toLowerCase();

  const header = (
    <>
      <BrowseHeader
        label="Explore suppliers"
        // NULL WHILE UNKNOWN, NEVER ZERO. A count of 0 above a
        // spinner is a fact that was never true, and it flashes on
        // every first load. BrowseHeader renders an ellipsis for
        // null and keeps the bar one height throughout.
        total={explore.isLoading ? null : visible.length}
        search={search}
        onSearch={setSearch}
        noun={{ one: "supplier", many: "suppliers" }}
      />
      {explore.kinds.length > 1 ? (
        <KindChipRow
          kinds={explore.kinds}
          selected={explore.kind}
          onSelect={explore.setKind}
        />
      ) : null}
    </>
  );

  // THE HEADER SURVIVES EVERY STATE, AND THAT IS THE FIX FOR A REAL
  // BUG. Loading and error used to return EARLY, before the header
  // existed -- so tapping a kind chip replaced the whole screen with a
  // bare spinner: no title, no chips, no way back except the system
  // back button, for as long as the fetch took. The reader had used a
  // control and the control vanished.
  //
  // IT IS ALSO WHY THE CHIPS ARE PART OF THE HEADER rather than part
  // of the list. A filter row that unmounts while its own result loads
  // is a filter row you cannot change your mind about.
  if (explore.isError) {
    return (
      <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
        {header}
        <ErrorState
          message="Couldn't load suppliers. Check your connection and try again."
          onRetry={explore.refetch}
        />
      </ScreenContainer>
    );
  }

  if (explore.isLoading) {
    return (
      <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
        {header}
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  return (
    // edges WITHOUT "top", AND NOT hasNativeHeader. BrowseHeader paints
    // the status-bar strip itself; hasNativeHeader would add sixteen
    // points of container background above it and the bar would wear
    // two colours. Same configuration every AppHeader screen uses.
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      {header}

      {visible.length === 0 ? (
        <View style={styles.centre}>
          <Text style={[styles.emptyTitle, { color: theme.colors.onSurface }]}>
            {search ? "Nothing matches" : `No ${activeLabel} yet`}
          </Text>
          <Text style={[styles.emptyBody, { color: theme.colors.onSurfaceVariant }]}>
            {/* NAMES THE REAL REASON. A supplier is missing from here
                because they are unverified or have no stock listed --
                not because anything failed -- and saying so is more
                useful than "nothing found". */}
            {search
              ? "No supplier in this list has that name. Clear the search to see them all."
              : "Suppliers appear here once they're verified and have stock listed. Invite one you already buy from and they'll show up."}
          </Text>
        </View>
      ) : (
        <FlatList
          data={visible}
          keyExtractor={(supplier) => supplier.id}
          contentContainerStyle={styles.content}
          ItemSeparatorComponent={() => (
            <View style={[styles.separator, { backgroundColor: theme.colors.outlineVariant }]} />
          )}
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
