import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Banknote, Receipt, Truck, Package2 } from "lucide-react-native";

import { formatCents } from "../../products/services/productMapper";
import { formatRelativeTime } from "@/utils/formatRelativeTime";
import { palette } from "@/theme/colors";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { DECLINE_REASON_LABELS } from "../types";
import type { OrderSummary } from "../types";

interface Props {
  order: OrderSummary;
  onPress: () => void;
}

const PAYMENT_ICONS = { CASH: Banknote, PROOF_OF_PAYMENT: Receipt, PAYFAST: Receipt };

/** The accent bar's own colour reads as the order's real state at a
 *  glance, across all three tabs -- amber for "still needs you,"
 *  green for "you said yes," red for "you said no" (or it timed
 *  out). Same "impossible to miss" reasoning as the original,
 *  New-only version, now genuinely meaningful in every tab instead
 *  of only the urgent one. */
const ACCENT_COLOR = {
  PENDING_SUPPLIER_APPROVAL: palette.warning,
  CONFIRMED: palette.success,
  DECLINED: palette.danger,
};

/**
 * One real, scannable card -- shared across all three tabs (New,
 * Approved, Declined). Shows the order reference, business name, and
 * the real person's own name -- identity at a glance, on purpose.
 * Phone, email, items, price breakdown, payment method, and delivery
 * details all stay on the order detail screen (tapping into a
 * specific order) -- confirmed directly: this card briefly carried
 * phone and email too, and was reverted after direct review found it
 * genuinely too much for a list view meant for a fast glance, not a
 * full contact card.
 */
export function OrderCard({ order, onPress }: Props) {
  const theme = useTheme();
  const PaymentIcon = order.paymentMethod ? PAYMENT_ICONS[order.paymentMethod] : Package2;
  const DeliveryIcon = order.deliveryType === "COLLECT" ? Package2 : Truck;
  const showBothNames = Boolean(order.buyerBusinessName && order.buyerName);

  return (
    <Pressable
      onPress={onPress}
      style={[styles.card, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}
      accessibilityRole="button"
      accessibilityLabel={`Order ${order.orderReference} from ${order.buyerBusinessName ?? order.buyerName}`}
    >
      <View style={[styles.accentBar, { backgroundColor: ACCENT_COLOR[order.status] }]} />

      <View style={styles.body}>
        <View style={styles.topRow}>
          <Text style={[styles.reference, { color: theme.colors.onSurface }]} numberOfLines={1}>
            {order.orderReference}
          </Text>
          <Text style={[styles.time, { color: theme.colors.onSurfaceVariant }]}>
            {order.submittedAt ? formatRelativeTime(order.submittedAt) : ""}
          </Text>
        </View>

        <Text style={[styles.buyer, { color: theme.colors.onSurface }]} numberOfLines={1}>
          {order.buyerBusinessName || order.buyerName || "A business"}
        </Text>
        {showBothNames && (
          <Text style={[styles.buyerSubtext, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
            {order.buyerName}
          </Text>
        )}

        {order.status === "DECLINED" && order.declineReason && (
          <View style={[styles.reasonBadge, { backgroundColor: theme.colors.errorContainer }]}>
            <Text style={[styles.reasonBadgeText, { color: theme.colors.error }]}>
              {DECLINE_REASON_LABELS[order.declineReason]}
            </Text>
          </View>
        )}

        <View style={styles.bottomRow}>
          <View style={styles.metaGroup}>
            <PaymentIcon size={14} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
            <Text style={[styles.metaText, { color: theme.colors.onSurfaceVariant }]}>
              {order.itemCount} {order.itemCount === 1 ? "item" : "items"}
            </Text>
            <DeliveryIcon size={14} color={theme.colors.onSurfaceVariant} strokeWidth={2} style={{ marginLeft: spacing.sm }} />
            <Text style={[styles.metaText, { color: theme.colors.onSurfaceVariant }]}>
              {order.deliveryType === "COLLECT" ? "Collect" : "Deliver"}
            </Text>
          </View>
          <Text style={[styles.total, { color: theme.colors.onSurface }]}>{formatCents(order.totalCents)}</Text>
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    borderWidth: 1,
    borderRadius: radius.md,
    marginHorizontal: spacing.md,
    marginBottom: spacing.sm,
    overflow: "hidden",
  },
  accentBar: { width: 4 },
  body: { flex: 1, padding: spacing.sm, gap: 4 },
  topRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  reference: { ...typography.bodySmall, fontWeight: "700", flexShrink: 1 },
  time: { ...typography.caption },
  buyer: { ...typography.body, fontWeight: "700" },
  buyerSubtext: { ...typography.bodySmall, marginTop: -2 },
  reasonBadge: { alignSelf: "flex-start", paddingHorizontal: spacing.sm, paddingVertical: 2, borderRadius: radius.pill, marginTop: 2 },
  reasonBadgeText: { ...typography.caption, fontWeight: "700" },
  bottomRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: 2 },
  metaGroup: { flexDirection: "row", alignItems: "center" },
  metaText: { ...typography.caption, marginLeft: 4 },
  total: { ...typography.body, fontWeight: "700" },
});
