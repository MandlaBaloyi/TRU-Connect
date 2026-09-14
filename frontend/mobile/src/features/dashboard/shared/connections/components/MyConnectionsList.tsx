import React from "react";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Users } from "lucide-react-native";

import { EmptyState } from "@/components/feedback/EmptyState";
import { ErrorState } from "@/components/feedback/ErrorState";
import { EntityAvatar } from "@/components/ui/EntityAvatar";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import { formatWhen } from "@/components/lists/CardListUI";

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
 *
 * INBOX ROWS, NOT CARDS -- these deliberately no longer use the shared
 * ListCard (components/lists/CardListUI.tsx) the way search results
 * still do, per direct product feedback ("make it like whatsapp
 * inbox"). A bordered card with a chevron reads as a settings row: a
 * thing you configure. A connection is a RELATIONSHIP, and every
 * messaging app renders those the same way -- edge-to-edge rows, a
 * large round photo, the name, and one quiet line beneath it,
 * separated by hairlines rather than boxed individually. Search
 * results keep ListCard on purpose: those genuinely ARE "pick one of
 * these" cards, which is a different thing from a list of people you
 * already know.
 *
 * The second line is the PERSON behind the business (ownerName), not
 * "Connected 3 weeks ago" as before -- when you're scanning your own
 * connections, "who is this" is the useful fact; the date something
 * was approved is not. It's omitted entirely when null (owner name is
 * optional at supplier sign-up), so the row collapses to one line
 * rather than leaving a blank second one.
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
      showsVerticalScrollIndicator={false}
      ItemSeparatorComponent={() => (
        // Inset to start where the text does, so the avatars read as a
        // single column rather than each row looking boxed off.
        <View style={[styles.separator, { backgroundColor: theme.colors.outlineVariant }]} />
      )}
      renderItem={({ item: connection }) => (
        <ConnectionRow
          connection={connection}
          // Never tappable without a real destination to send it to --
          // a row with no other_party_id (the rare edge case where the
          // other party's own profile doesn't exist yet, see
          // connection_list_service.py's own other_party_id docstring)
          // stays a plain display row rather than becoming a broken
          // link.
          onPress={onPressConnection && connection.otherPartyId ? () => onPressConnection(connection) : undefined}
        />
      )}
    />
  );
}


/**
 * The one line that turns a contact into a LEDGER ENTRY (V2_04 2.3).
 *
 * ONE LINE, NOT THREE FACTS. A row showing order count AND typical gap
 * AND last order AND open status is a table, and a shopkeeper scanning
 * for who to phone reads none of it. So the row says the single most
 * actionable thing true right now, in the same priority the server
 * sorted by: somebody waiting, then somebody late, then plain history.
 *
 * RETURNS null RATHER THAN "No orders yet". A connection with no
 * history is the normal state straight after connecting, and captioning
 * it would be the app telling somebody how little they have on the day
 * they arrive -- the same rule the Community feed follows by returning
 * no card at all.
 */
function ledgerLine(connection: ConnectionSummary): { text: string; emphasis: boolean } | null {
  if (connection.openOrder) return { text: "Order waiting", emphasis: true };
  if (connection.isOverdue && connection.lastOrderAt) {
    return { text: `Due to reorder · last ordered ${formatWhen(connection.lastOrderAt)}`, emphasis: true };
  }
  if (connection.lastOrderAt) {
    return { text: `Last ordered ${formatWhen(connection.lastOrderAt)}`, emphasis: false };
  }
  return null;
}

function ConnectionRow({ connection, onPress }: { connection: ConnectionSummary; onPress?: () => void }) {
  const theme = useTheme();
  const ledger = ledgerLine(connection);

  const content = (
    <>
      <EntityAvatar name={connection.name} photoUrl={connection.photoUrl} size={52} />
      <View style={styles.rowText}>
        <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={1}>
          {connection.name}
        </Text>
        {connection.ownerName && (
          <Text style={[styles.owner, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
            {connection.ownerName}
          </Text>
        )}
        {ledger && (
          <Text
            style={[
              styles.ledger,
              { color: ledger.emphasis ? theme.colors.primary : theme.colors.onSurfaceVariant },
            ]}
            numberOfLines={1}
          >
            {ledger.text}
          </Text>
        )}
      </View>
    </>
  );

  if (!onPress) {
    return <View style={styles.row}>{content}</View>;
  }

  return (
    <Pressable
      onPress={onPress}
      android_ripple={{ color: theme.colors.surfaceVariant }}
      style={({ pressed }) => [styles.row, { backgroundColor: pressed ? theme.colors.surfaceVariant : "transparent" }]}
      accessibilityRole="button"
      accessibilityLabel={[connection.name, connection.ownerName, ledger?.text]
        .filter(Boolean)
        .join(", ")}
    >
      {content}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  ledger: { ...typography.caption, marginTop: 2 },
  centre: { flex: 1, alignItems: "center", justifyContent: "center", paddingTop: spacing.xxl },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    minHeight: 72,
  },
  rowText: { flex: 1, gap: 2 },
  name: { ...typography.body, fontWeight: "700", fontSize: 16 },
  owner: { ...typography.bodySmall },
  // Starts past the avatar (16 padding + 52 avatar + 16 gap), matching
  // how every inbox list insets its dividers.
  separator: { height: StyleSheet.hairlineWidth, marginLeft: 84 },
});
