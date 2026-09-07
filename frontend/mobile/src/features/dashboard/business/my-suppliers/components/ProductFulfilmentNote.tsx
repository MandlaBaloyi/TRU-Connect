import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { CircleCheck, Truck, Wallet } from "lucide-react-native";

import { formatCents } from "../../../supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * The supplier's terms, answered against THIS cart: will this order
 * reach their minimum, and will they bring it to you.
 *
 * PLACED DIRECTLY UNDER "In stock", inside a collapsible section
 * titled with the supplier's own name (see requirementsTitle in
 * SupplierProductDetailScreen).
 *
 * THIS POSITION HAS MOVED TWICE, and the history is the reasoning.
 * It began under the price, was moved to the bottom above the buy bar
 * because terms are checked at commit time and up top they competed
 * with the price and pushed the description down — then moved back to
 * the top on direct feedback. The bottom placement was wrong for a
 * reason the first move missed: a business that only discovers a R500
 * minimum after building a cart has been made to waste the whole
 * visit, and at that point the number reads as a rejection rather than
 * an instruction. "Can I get it" and "what does it take to get it" are
 * one question. Collapsing solves what the first move was actually
 * reaching for — it can be folded away by anyone who already knows.
 *
 * THE SHORTFALL IS COMPUTED AGAINST THE WHOLE CART, not this product
 * alone. A business with R200 already in the cart looking at a R150
 * item is R150 from a R500 minimum, not R350 — the latter is
 * arithmetic they'd have to redo, and makes a reachable minimum look
 * out of reach.
 *
 * THE COST OF SITTING AT THE TOP, accepted knowingly: the shortfall is
 * still live against the cart, but the quantity stepper is now far
 * below it, so pressing + no longer visibly closes the gap on screen.
 * Seeing the requirement BEFORE building a cart beats watching it
 * update while building one.
 *
 * ON THE STYLING — these were filled tinted blocks using
 * theme.colors.errorContainer / secondaryContainer. Neither is defined
 * in this app's theme, so both fell through to react-native-paper's
 * MD3 defaults: a muted pink-brown that belongs to no palette here and
 * read as muddy against the white page. Reported directly as "that
 * brown colour is not good".
 *
 * Now they use the app's own card language — surface, hairline border,
 * with COLOUR CARRIED BY THE ICON and the amount rather than a filled
 * background. Same treatment as ProfileCard and the profile's own
 * fulfilment block, so a business meets one visual idea for "a fact
 * about this supplier" instead of three.
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
  // null means the supplier hasn't stated their terms — saying nothing
  // is the honest answer, never "collection only" on their behalf.
  const showDelivery = offersDelivery !== null;

  if (!showMinimum && !showDelivery) return null;

  const shortfallColour = shortfall > 0 ? theme.colors.error : theme.colors.secondary;

  return (
    <View style={styles.wrap}>
      <View
        style={[styles.card, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}
      >
        {showMinimum && (
          <View style={styles.row}>
            <View style={[styles.iconWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
              {shortfall > 0 ? (
                <Wallet size={16} color={shortfallColour} strokeWidth={2.2} />
              ) : (
                <CircleCheck size={16} color={shortfallColour} strokeWidth={2.2} />
              )}
            </View>
            {/* LEADS WITH THE FACT, then what it means for this cart.
                It used to open on the instruction ("Add R150 more to
                reach this supplier's R500.00 minimum order") -- one
                run-on line carrying two amounts, where the number that
                matters most, the minimum itself, arrived last and
                unlabelled. Now the term is stated first and the
                consequence follows as its own sentence, so the row
                reads the same whether the minimum is met or not. */}
            <Text style={[styles.text, { color: theme.colors.onSurfaceVariant }]}>
              <Text style={styles.strong}>Minimum order {formatCents(minimumOrderCents!)}</Text>
              {shortfall > 0 ? (
                <>
                  {" — add "}
                  <Text style={[styles.strong, { color: shortfallColour }]}>{formatCents(shortfall)}</Text>
                  {" more to reach it."}
                </>
              ) : (
                <>
                  {" — "}
                  <Text style={[styles.strong, { color: shortfallColour }]}>your order meets it</Text>
                  {"."}
                </>
              )}
            </Text>
          </View>
        )}

        {showMinimum && showDelivery && (
          <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />
        )}

        {showDelivery && (
          <View style={styles.row}>
            <View style={[styles.iconWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
              <Truck size={16} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />
            </View>
            {/* "Delivers" alone was a fragment with no subject -- it
                read as a label, not a statement, and sat oddly beside
                the fuller "Collection only" line under it. Both now
                name what the supplier offers and finish the sentence
                with a full stop, matching the minimum-order row above. */}
            <Text style={[styles.text, { color: theme.colors.onSurfaceVariant }]}>
              {offersDelivery ? (
                <>
                  <Text style={styles.strong}>Delivery available</Text>
                  {" — choose delivery or collection at checkout."}
                </>
              ) : (
                <>
                  <Text style={styles.strong}>Collection only</Text>
                  {" — you collect this order from the supplier."}
                </>
              )}
            </Text>
          </View>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  // NO horizontal padding of its own: this now renders inside the
  // screen's own padded fulfilment wrapper, inside an AccordionSection.
  // It used to sit directly in the scroll view and pad itself; keeping
  // that would double the inset against every other block.
  wrap: {},
  card: { borderRadius: radius.lg, borderWidth: 1, paddingVertical: spacing.xs },
  row: { flexDirection: "row", alignItems: "center", gap: spacing.md, padding: spacing.sm + 2 },
  iconWrap: { width: 32, height: 32, borderRadius: 16, alignItems: "center", justifyContent: "center" },
  text: { ...typography.bodySmall, flex: 1, lineHeight: 18 },
  strong: { fontWeight: "800" },
  divider: { height: StyleSheet.hairlineWidth, marginLeft: 56 },
});
