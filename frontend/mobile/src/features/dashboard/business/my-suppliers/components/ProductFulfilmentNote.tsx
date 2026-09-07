import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { CircleCheck, Truck, Wallet } from "lucide-react-native";

import { formatCents } from "../../../supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * The supplier's terms, on the product page, answered against THIS
 * cart: will it reach their minimum, and will they bring it to you.
 *
 * WHY IT'S HERE AND NOT ONLY ON THE PROFILE. Both facts already existed
 * on the brand profile and were enforced at checkout — but the product
 * page is where a business actually decides to add something. Finding
 * out at checkout that you're R300 short, or that this supplier doesn't
 * deliver, means having built the whole cart first. That's the same
 * friction removed from the delivery flow earlier, still sitting one
 * screen upstream.
 *
 * THE SHORTFALL IS COMPUTED AGAINST THE WHOLE CART, not this product
 * alone. A business with R200 already in the cart looking at a R150
 * item is R150 away from a R500 minimum, not R350 — telling them the
 * latter would be arithmetic they'd have to redo themselves, and would
 * make a reachable minimum look out of reach.
 *
 * It also moves with the QUANTITY STEPPER, so pressing + visibly closes
 * the gap. That's the point: it turns a blocker into an instruction.
 */
export function ProductFulfilmentNote({
  offersDelivery,
  minimumOrderCents,
  cartTotalCents,
  lineTotalCents,
}: {
  offersDelivery: boolean | null;
  minimumOrderCents: number | null;
  /** What's in the cart for this supplier already. 0 when empty. */
  cartTotalCents: number;
  /** This product at the currently-chosen quantity. */
  lineTotalCents: number;
}) {
  const theme = useTheme();

  const projected = cartTotalCents + lineTotalCents;
  const shortfall = minimumOrderCents !== null ? Math.max(0, minimumOrderCents - projected) : 0;
  const showMinimum = minimumOrderCents !== null;
  // null means the supplier hasn't stated their terms -- saying nothing
  // is the honest answer, never "collection only" on their behalf.
  const showDelivery = offersDelivery !== null;

  if (!showMinimum && !showDelivery) return null;

  return (
    <View style={styles.wrap}>
      {showMinimum && (
        <View
          style={[
            styles.row,
            {
              backgroundColor: shortfall > 0 ? theme.colors.errorContainer : theme.colors.secondaryContainer,
            },
          ]}
        >
          {shortfall > 0 ? (
            <Wallet size={16} color={theme.colors.error} strokeWidth={2.2} />
          ) : (
            <CircleCheck size={16} color={theme.colors.secondary} strokeWidth={2.2} />
          )}
          <Text
            style={[
              styles.text,
              { color: shortfall > 0 ? theme.colors.error : theme.colors.secondary },
            ]}
          >
            {shortfall > 0 ? (
              <>
                Add <Text style={styles.strong}>{formatCents(shortfall)}</Text> more to reach this
                supplier&apos;s {formatCents(minimumOrderCents!)} minimum order
              </>
            ) : (
              <>This order meets their {formatCents(minimumOrderCents!)} minimum</>
            )}
          </Text>
        </View>
      )}

      {showDelivery && (
        <View style={[styles.row, { backgroundColor: theme.colors.surfaceVariant }]}>
          <Truck size={16} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />
          <Text style={[styles.text, { color: theme.colors.onSurfaceVariant }]}>
            {offersDelivery
              ? "This supplier delivers — you choose delivery or collection at checkout"
              : "Collection only — you'll collect this order from the supplier"}
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { paddingHorizontal: spacing.md, gap: spacing.xs, marginTop: spacing.sm },
  row: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: spacing.sm,
    padding: spacing.sm + 2,
    borderRadius: radius.md,
  },
  text: { ...typography.bodySmall, flex: 1, lineHeight: 18 },
  strong: { fontWeight: "800" },
});
