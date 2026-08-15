import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Users } from "lucide-react-native";

import { EmptyState } from "@/components/feedback/EmptyState";
import { ErrorState } from "@/components/feedback/ErrorState";
import { ListCard, formatWhen } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";

import { useMyConnections } from "../hooks/useMyConnections";

/**
 * My Connections — the shared list body both Community tabs render.
 * ACTIVE connections only (see this feature's own types.ts). One
 * component, one hook, one backend call, used identically by both
 * roles — see types.ts's own note on why this stays a single shared
 * feature rather than two role-specific copies.
 */
export function MyConnectionsList() {
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
    <ScrollView contentContainerStyle={styles.list} showsVerticalScrollIndicator={false}>
      {connections.map((connection) => (
        <ListCard
          key={connection.id}
          icon={(c) => <Users size={20} color={c} />}
          title={connection.name}
          subtitle={connection.connectedSince ? `Connected ${formatWhen(connection.connectedSince)}` : undefined}
        />
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center", paddingTop: spacing.xxl },
  list: { padding: spacing.md, gap: spacing.sm },
});
