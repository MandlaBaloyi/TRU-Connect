import React from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Clock, UserPlus, UserSearch } from "lucide-react-native";

import { EmptyState } from "@/components/feedback/EmptyState";
import { ErrorState } from "@/components/feedback/ErrorState";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useSupplierSearch } from "../hooks/useSupplierSearch";
import { useRecentSearches } from "../hooks/useRecentSearches";
import { SupplierResultCard } from "./SupplierResultCard";

/**
 * Everything FindSupplierScreen.tsx used to own BELOW its own search
 * input — extracted so the search input itself can move into
 * Community's own top bar (per direct product feedback: "the search
 * must move into the top bar", removing "Find Supplier" as a
 * separately-named destination) while this body still works exactly
 * as it did as a full screen. `query` is now a prop, controlled by
 * whoever owns the input (Community's own search-mode state) rather
 * than local state here.
 */
export function InlineSupplierSearch({ query }: { query: string }) {
  const router = useRouter();
  const theme = useTheme();
  const { results, isSearching, isError, hasQuery, isEmpty } = useSupplierSearch(query);
  const { recentSearches } = useRecentSearches();

  if (!hasQuery) {
    return (
      <ScrollView contentContainerStyle={styles.preSearch} keyboardShouldPersistTaps="handled">
        {recentSearches.length === 0 ? (
          <EmptyState
            icon={<UserSearch size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
            message="Search for a supplier you already work with, by their business name."
          />
        ) : (
          <View style={styles.recentSection}>
            <Text style={[styles.sectionTitle, { color: theme.colors.onSurfaceVariant }]}>Recent searches</Text>
            {recentSearches.map((recent) => (
              <Pressable
                key={recent.id}
                onPress={() => router.push(`/business/find-supplier/${recent.id}` as any)}
                style={({ pressed }) => [
                  styles.recentRow,
                  { borderColor: theme.colors.outlineVariant, opacity: pressed ? 0.7 : 1 },
                ]}
                accessibilityRole="button"
                accessibilityLabel={recent.businessName}
              >
                <Clock size={16} color={theme.colors.onSurfaceVariant} />
                <Text style={[styles.recentLabel, { color: theme.colors.onSurface }]}>{recent.businessName}</Text>
              </Pressable>
            ))}
          </View>
        )}

        <View style={styles.inviteBlock}>
          <Text style={[styles.inviteQuestion, { color: theme.colors.onSurfaceVariant }]}>
            Can't find your supplier?
          </Text>
          <Pressable
            onPress={() => router.push("/business/find-supplier/invite" as any)}
            style={styles.inviteRow}
            accessibilityRole="button"
            accessibilityLabel="Invite Supplier"
          >
            <UserPlus size={16} color={theme.colors.primary} strokeWidth={2.2} />
            <Text style={[styles.inviteText, { color: theme.colors.primary }]}>Invite Supplier</Text>
          </Pressable>
        </View>
      </ScrollView>
    );
  }

  if (isSearching) {
    return (
      <View style={styles.centre}>
        <ActivityIndicator color={theme.colors.primary} />
      </View>
    );
  }

  if (isError) {
    return <ErrorState message="Couldn't search right now. Check your connection and try again." />;
  }

  if (isEmpty) {
    return (
      <ScrollView contentContainerStyle={styles.preSearch}>
        <EmptyState
          icon={<UserSearch size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
          message="No supplier found with that name. Double-check what you entered, or invite them below."
        />
        <View style={styles.inviteBlock}>
          <Pressable
            onPress={() => router.push("/business/find-supplier/invite" as any)}
            style={styles.inviteRow}
            accessibilityRole="button"
            accessibilityLabel="Invite Supplier"
          >
            <UserPlus size={16} color={theme.colors.primary} strokeWidth={2.2} />
            <Text style={[styles.inviteText, { color: theme.colors.primary }]}>Invite Supplier</Text>
          </Pressable>
        </View>
      </ScrollView>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.results} keyboardShouldPersistTaps="handled">
      <Text style={[styles.resultCount, { color: theme.colors.onSurfaceVariant }]}>
        {results.length} result{results.length === 1 ? "" : "s"}
      </Text>
      <View style={styles.grid}>
        {results.map((result) => (
          <SupplierResultCard
            key={result.id}
            result={result}
            onPress={() => router.push(`/business/find-supplier/${result.id}` as any)}
          />
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  preSearch: { flexGrow: 1, padding: spacing.md, gap: spacing.lg },
  recentSection: { gap: spacing.xs },
  sectionTitle: { ...typography.bodySmall, fontWeight: "700", textTransform: "uppercase", letterSpacing: 0.5 },
  recentRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.xs,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  recentLabel: { ...typography.body },
  inviteBlock: { alignItems: "center", gap: spacing.xs, marginTop: "auto", paddingTop: spacing.lg },
  inviteQuestion: { ...typography.bodySmall },
  inviteRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs, minHeight: 40 },
  inviteText: { ...typography.body, fontWeight: "700" },
  results: { padding: spacing.md, gap: spacing.sm },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  resultCount: { ...typography.bodySmall, fontWeight: "600", marginBottom: spacing.xs },
});
