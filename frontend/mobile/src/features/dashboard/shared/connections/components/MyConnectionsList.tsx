import React from "react";
import { ActivityIndicator, FlatList, StyleSheet, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Users } from "lucide-react-native";

import { EmptyState } from "@/components/feedback/EmptyState";
import { ErrorState } from "@/components/feedback/ErrorState";
import { ListCard, formatWhen } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";

import { useMyConnections } from "../hooks/useMyConnections";
import type { ConnectionSummary } from "../types";

/**
 * My Connections — the shared list body both Community tabs render.
 * ACTIVE connections only (see this feature's own types.ts). One
 * component, one hook, one backend call, used identically by both
 * roles — see types.ts's own note on why this stays a single shared
 * feature rather than two role-specific copies.
 *
 * FlatList, not ScrollView -- same real virtualization fix applied to
 * both search results screens (InlineSupplierSearch.tsx /
 * InlineBusinessSearch.tsx): only rows actually near-visible get
 * rendered, rather than every connection's full component tree at
 * once regardless of scroll position.
 *
 * onPressConnection IS DELIBERATELY A CALLBACK, NOT ROUTING BUILT IN
 * HERE -- where a tap leads differs by role (a business goes to that
 * supplier's own products; a supplier goes to that business's own
 * profile), and this component has no way to know which role is
 * viewing it. Each role's own community.tsx screen supplies its own
 * navigation, keeping this list genuinely role-agnostic rather than
 * branching internally on a role it was never told. Rows render as
 * plain, non-tappable display cards when omitted -- never assume a
 * destination exists.
 */
export function MyConnectionsList({
  onPressConnection,
}: {
  onPressConnection?: (connection: ConnectionSummary) => void;
}) {
  const theme = useTheme();
  const { connections, isLoading, isError, refetch } = useMyConnections();

  if (isLoading) {
    return (
      <View style={styles.centre}>
        <ActivityIndicator color={theme.colors.primary} />
      </View>
    );
  }

  if (isError) {
    return <ErrorState message="Couldn't load your connections. Check your connection and try again." onRetry={refetch} />;
  }

  if (connections.length === 0) {
    return (
      <EmptyState
        icon={<Users size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
        message="No connections yet. Once a connection request is approved, they'll show up here."
      />
    );
  }

  return (
    <FlatList
      data={connections}
      keyExtractor={(connection) => connection.id}
      contentContainerStyle={styles.list}
      showsVerticalScrollIndicator={false}
      renderItem={({ item: connection }) => (
        <ListCard
          icon={(c) => <Users size={20} color={c} />}
          title={connection.name}
          subtitle={connection.connectedSince ? `Connected ${formatWhen(connection.connectedSince)}` : undefined}
          // Never tappable without a real destination to send it to --
          // a row with no other_party_id (the rare edge case where the
          // other party's own profile doesn't exist yet, see
          // connections_service.py's own other_party_id docstring)
          // stays a plain display row rather than becoming a broken
          // link.
          onPress={onPressConnection && connection.otherPartyId ? () => onPressConnection(connection) : undefined}
        />
      )}
    />
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center", paddingTop: spacing.xxl },
  list: { padding: spacing.md, gap: spacing.sm },
});
