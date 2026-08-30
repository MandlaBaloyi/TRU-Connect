import React from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { UserX } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { EmptyState } from "@/components/feedback/EmptyState";
import { ErrorState } from "@/components/feedback/ErrorState";
import { ListCard, formatWhen } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useEndedConnections } from "../hooks/useEndedConnections";
import { DISCONNECT_REASONS } from "../types";

function reasonLabel(reason: string | null): string | null {
  if (!reason) return null;
  return DISCONNECT_REASONS.find((option: { value: string; label: string }) => option.value === reason)?.label ?? reason;
}

/**
 * "Who have I disconnected from" -- reached from the Community tab's
 * own "⋮" menu (CommunityOverflowMenu.tsx). Business-only today, same
 * as list_ended_connections' own backend docstring -- no equivalent
 * supplier-side flow exists yet.
 *
 * Lives under shared/connections/ (not business/), matching WHERE the
 * rest of this feature's data layer already lives (types.ts,
 * hooks/useEndedConnections.ts) -- even though only the business side
 * reaches this screen today, same precedent as MyConnectionsList.tsx
 * itself already being shared even though some of what it does is
 * role-conditional.
 *
 * Read-only -- no "reconnect" action here. Reconnecting after a
 * disconnect is a real, separate question (does it reuse the same row,
 * does retry-limit logic apply) that wasn't part of what this pass
 * was asked to build; this screen is deliberately just the history.
 */
export default function DisconnectedSuppliersScreen() {
  const theme = useTheme();
  const { connections, isLoading, isError, refetch } = useEndedConnections();

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
        <ErrorState message="Couldn't load this. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  if (connections.length === 0) {
    return (
      <ScreenContainer hasNativeHeader>
        <EmptyState
          icon={<UserX size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
          message="You haven't disconnected from any suppliers."
        />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader>
      <View style={styles.list}>
        {connections.map((connection) => {
          const reason = reasonLabel(connection.endedReason);
          const subtitleParts = [
            reason,
            connection.endedAt ? `Disconnected ${formatWhen(connection.endedAt)}` : null,
          ].filter((part): part is string => Boolean(part));

          return (
            <View key={connection.id} style={styles.item}>
              <ListCard
                icon={(c) => <UserX size={20} color={c} />}
                title={connection.name}
                subtitle={subtitleParts.length > 0 ? subtitleParts.join(" · ") : undefined}
              />
              {connection.endedDetails && (
                <Text style={[styles.details, { color: theme.colors.onSurfaceVariant }]}>
                  {connection.endedDetails}
                </Text>
              )}
            </View>
          );
        })}
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  list: { padding: spacing.md, gap: spacing.sm },
  item: { gap: 4 },
  details: { ...typography.bodySmall, paddingLeft: spacing.md + 44 + spacing.sm, marginTop: -4 },
});
