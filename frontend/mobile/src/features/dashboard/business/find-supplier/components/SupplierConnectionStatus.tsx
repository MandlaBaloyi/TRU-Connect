import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { CircleAlert, CircleCheck, Clock, Link2Off, UserPlus } from "lucide-react-native";

import { InfoHint } from "@/components/ui/InfoHint";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { ConnectionInitiator, ConnectionStatus } from "../types";

/**
 * The connection state, as a STRUCTURED status rather than a loose
 * sentence.
 *
 * WHAT THIS REPLACED, and why: each state used to render one free-text
 * banner ("You're connected — you can place stock orders with this
 * supplier."). Three problems with that. It buried the actual state
 * inside prose, so there was nothing to scan for. It couldn't
 * distinguish the two completely different meanings of PENDING. And it
 * gave a business no fixed vocabulary — the labels here ("Connected",
 * "Disconnected", "Waiting for you to accept") are a closed set, and
 * the ⋮ "About connections" sheet lists every one of them with what to
 * do about it.
 *
 * THE PENDING SPLIT IS THE REAL POINT. A pending request means
 * "waiting for them" if the business sent it, and "waiting for YOU" if
 * the supplier did — opposite states, identical text before. The
 * backend now returns connectionInitiatedBy precisely so this
 * component can tell them apart; a business sitting on an unanswered
 * supplier request had no way to know it was their move.
 *
 * ENDED reads as "Disconnected" and stays actionable: disconnecting is
 * not a dead end, you can reconnect (the backend's own retry window
 * governs how often).
 *
 * THE EXPLANATION LIVES BEHIND AN ⓘ. The state itself is the label;
 * what it means opens on tap. A permanent sentence under every status
 * meant a business read it once and then paid for it on every visit.
 *
 * WEIGHT FOLLOWS URGENCY -- the point of `prominence`. Every state used
 * to render as the same full-width bordered card with an icon circle
 * and an accent rule, differing only in colour. That made "Connected"
 * -- the calm state where there is nothing to do -- as loud as
 * "Waiting for you to accept", and left a wide dead gap between a
 * one-word label and a right-aligned ⓘ. Now:
 *
 *   QUIET (nothing to do: Connected, waiting on THEM) -- one slim
 *   inline row, matching the fulfilment section's own row height.
 *
 *   PROMINENT (your move: waiting on YOU, declined, not connected,
 *   disconnected) -- the full card, and the instruction shown INLINE
 *   rather than behind the ⓘ, because a state that needs action should
 *   say what the action is without a tap.
 *
 * Colour still travels with text and an icon, never alone.
 */

type Tone = "positive" | "waiting" | "attention" | "neutral";

type IconType = React.ComponentType<{ size: number; color: string; strokeWidth: number }>;

interface StatusView {
  label: string;
  detail: string;
  tone: Tone;
  /** Resolved here rather than mapped from `tone`, because two states
   *  share a tone but mean different things -- "Disconnected" and "Not
   *  connected" are both neutral, and a broken-link icon vs an
   *  add-person icon is exactly what tells them apart at a glance. */
  icon: IconType;
  /** True when the business itself can act from here. */
  showRequestButton: boolean;
  /** How much room this state earns -- see the "weight follows
   *  urgency" note above. Derived from the state itself, not passed
   *  in, so the rule lives in one place. */
  prominence: "quiet" | "prominent";
}

export function resolveConnectionView(
  status: ConnectionStatus,
  initiatedBy: ConnectionInitiator | null,
  supplierName: string
): StatusView {
  switch (status) {
    case "ACTIVE":
      return {
        label: "Connected",
        prominence: "quiet",
        icon: CircleCheck,
        detail: `You can place stock orders with ${supplierName}.`,
        tone: "positive",
        showRequestButton: false,
      };
    case "PENDING":
      // The one state whose meaning genuinely depends on who started it.
      return initiatedBy === "SUPPLIER"
        ? {
            label: "Waiting for you to accept",
        prominence: "prominent",
        icon: CircleAlert,
            detail: `${supplierName} asked to connect with you. Open Supplier requests to accept or decline.`,
            tone: "attention",
            showRequestButton: false,
          }
        : {
            label: "Waiting for supplier to accept",
        prominence: "quiet",
        icon: Clock,
            detail: `Your request was sent. ${supplierName} hasn't responded yet.`,
            tone: "waiting",
            showRequestButton: false,
          };
    case "DECLINED":
      return {
        label: "Request declined",
        prominence: "prominent",
        icon: CircleAlert,
        detail: `${supplierName} declined your connection request.`,
        tone: "attention",
        showRequestButton: false,
      };
    case "ENDED":
      return {
        label: "Disconnected",
        prominence: "prominent",
        icon: Link2Off,
        detail: `You're no longer connected to ${supplierName}. You can request to connect again.`,
        tone: "neutral",
        showRequestButton: true,
      };
    default:
      return {
        label: "Not connected",
        prominence: "prominent",
        icon: UserPlus,
        detail: `Request a connection to place stock orders with ${supplierName}.`,
        tone: "neutral",
        showRequestButton: true,
      };
  }
}

export function SupplierConnectionStatus({
  status,
  initiatedBy,
  supplierName,
  onRequest,
  isSubmitting,
}: {
  status: ConnectionStatus;
  initiatedBy: ConnectionInitiator | null;
  supplierName: string;
  onRequest: () => void;
  isSubmitting: boolean;
}) {
  const theme = useTheme();
  const view = resolveConnectionView(status, initiatedBy, supplierName);

  // ONE accent colour per state, carried by the icon and a thin left
  // rule -- not a full tinted block. The earlier version filled the
  // whole card with the tone colour and inverted a pill inside it,
  // which shouted louder than the products it sits above and made
  // "Connected" (the calm, normal state) the single loudest thing on
  // the screen. Colour AND text still travel together, so the state is
  // never carried by colour alone.
  const accent: Record<Tone, string> = {
    positive: theme.colors.secondary,
    waiting: theme.colors.onSurfaceVariant,
    attention: theme.colors.error,
    neutral: theme.colors.onSurfaceVariant,
  };
  const colour = accent[view.tone];
  const Icon = view.icon;

  // QUIET: nothing for the business to do here -- one slim inline row,
  // no card, no accent rule, no dead gap. The ⓘ sits right after the
  // label rather than floating at the far edge.
  if (view.prominence === "quiet") {
    return (
      <View style={styles.quietRow}>
        <Icon size={16} color={colour} strokeWidth={2.4} />
        <Text style={[styles.quietLabel, { color: colour }]}>{view.label}</Text>
        <InfoHint title={view.label} body={view.detail} size={15} />
      </View>
    );
  }

  // PROMINENT: the business's move. Full card, and the instruction is
  // shown INLINE -- a state that needs action shouldn't hide what the
  // action is behind a tap.
  return (
    <View style={styles.wrap}>
      <View
        style={[
          styles.card,
          { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant },
        ]}
      >
        <View style={[styles.accentRule, { backgroundColor: colour }]} />
        <View style={[styles.iconWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
          <Icon size={18} color={colour} strokeWidth={2.2} />
        </View>
        <View style={styles.text}>
          <Text style={[styles.label, { color: colour }]}>{view.label}</Text>
          <Text style={[styles.detail, { color: theme.colors.onSurfaceVariant }]}>{view.detail}</Text>
        </View>
      </View>

      {view.showRequestButton && (
        <PrimaryButton onPress={onRequest} loading={isSubmitting} disabled={isSubmitting}>
          {status === "ENDED" ? "Request to connect again" : "Request Connection"}
        </PrimaryButton>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.sm },
  card: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: spacing.md,
    padding: spacing.md,
    paddingLeft: spacing.md + 4,
    borderRadius: radius.lg,
    borderWidth: 1,
    overflow: "hidden",
  },
  // The state's colour as a 4px rule down the card's leading edge --
  // enough to be scannable in a list of blocks without tinting a whole
  // surface.
  accentRule: { position: "absolute", left: 0, top: 0, bottom: 0, width: 4 },
  iconWrap: { width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center" },
  text: { flex: 1, gap: 2 },
  label: { ...typography.body, fontWeight: "700" },
  detail: { ...typography.bodySmall, lineHeight: 19 },
  // Matches the fulfilment accordion's own header row, so the two read
  // as the same kind of thing rather than two different systems.
  quietRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs, paddingVertical: spacing.xs },
  quietLabel: { ...typography.body, fontWeight: "700" },
});
