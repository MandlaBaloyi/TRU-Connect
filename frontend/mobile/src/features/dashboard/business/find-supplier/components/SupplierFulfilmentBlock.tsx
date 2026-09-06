import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { MapPin, Truck, Wallet } from "lucide-react-native";

import { AccordionSection } from "@/components/ui/AccordionSection";
import { InfoHint } from "@/components/ui/InfoHint";
import { formatCents } from "../../../supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { SupplierCollectionAddress } from "../types";

/**
 * "Can I actually buy from these people, and how do I get the stock?"
 * — the practical terms an informal business needs BEFORE building a
 * cart, in one block: delivery, minimum order, and where to collect.
 *
 * WHY THESE THREE TOGETHER: they're one decision, not three facts. A
 * spaza owner planning a stock run is asking a single question — will
 * this arrive, or am I driving there, and is it worth the trip. Split
 * across the screen they'd have to assemble the answer themselves.
 *
 * WHAT'S GATED AND WHAT ISN'T, deliberately different per row:
 *   - delivery + minimum order are UNGATED. A business needs them
 *     while DECIDING whether to connect at all; hiding them until
 *     after connection means finding out too late.
 *   - the collection ADDRESS is connection-only (backend gate). It's a
 *     real street address, not a shopfront term.
 * So a not-yet-connected business sees the terms but not the address,
 * which is the intended asymmetry rather than an inconsistency.
 *
 * DELIVERY IS TRI-STATE, and all three are handled distinctly:
 *   true  -> "Delivery available"
 *   false -> "Collection only". A real, useful answer, NOT an empty
 *            state to hide: it's exactly what tells a business without
 *            transport to look elsewhere.
 *   null  -> nothing at all. The supplier hasn't said, and asserting
 *            "collection only" on their behalf would state something
 *            they never did. This distinction is not cosmetic -- it's
 *            the bug a plain boolean caused (see the column's own
 *            comment in supplier_profile.py).
 *
 * Minimum order works the same way: null genuinely means "no minimum",
 * so it shows nothing rather than claiming "R0".
 *
 * The whole section disappears when none of the three rows has
 * anything real to say.
 *
 * COLLAPSIBLE, AND THE EXPLANATIONS MOVED BEHIND AN ⓘ. Expanded, with
 * a sentence under every row, this card pushed the supplier's actual
 * PRODUCTS below the fold on a phone -- process copy outranking the
 * thing the screen is for. The row titles now carry the facts
 * ("Delivery available", "Minimum order R500.00") and the ⓘ carries
 * what they mean, so a business who already knows never pays for the
 * explanation.
 */
export function SupplierFulfilmentBlock({
  offersDelivery,
  minimumOrderCents,
  address,
}: {
  offersDelivery: boolean | null;
  minimumOrderCents: number | null;
  address: SupplierCollectionAddress | null;
}) {
  const theme = useTheme();

  const addressLines = address
    ? [
        address.building,
        address.street,
        address.suburb,
        [address.city, address.province].filter(Boolean).join(", "),
        address.postalCode,
      ].filter((part): part is string => Boolean(part && part.trim()))
    : [];

  const showDelivery = offersDelivery !== null;
  const showMinimum = minimumOrderCents !== null;
  const showAddress = addressLines.length > 0;

  // Nothing real to say -> no empty card.
  if (!showDelivery && !showMinimum && !showAddress) return null;

  return (
    <View style={styles.wrap}>
      <AccordionSection
        title="Delivery & collection"
        // COLLAPSED BY DEFAULT, unlike the product screen's accordions.
        // These are terms you check once before your first order, not
        // something you re-read every visit -- and expanded, this
        // section pushed the supplier's actual products below the fold.
        defaultExpanded={false}
        titleAccessory={
          <InfoHint
            title="Delivery & collection"
            body={[
              "How this supplier fulfils orders, and what it costs to place one.",
              "They set these themselves. Delivery and minimum order are shown to anyone; the collection address only to businesses they're connected with.",
            ]}
          />
        }
      >
      <View
        style={[styles.card, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}
      >
        {showDelivery && (
          <Row
            icon={<Truck size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />}
            title={offersDelivery ? "Delivery available" : "Collection only"}
            hint={
              <InfoHint
                title={offersDelivery ? "Delivery available" : "Collection only"}
                body={
                  offersDelivery
                    ? "This supplier can deliver your order. You choose delivery or collection when you check out."
                    : "This supplier doesn't deliver. You'll collect your order from them, and only Collect is available at checkout."
                }
              />
            }
          />
        )}

        {showMinimum && (
          <>
            {showDelivery && <Divider />}
            <Row
              icon={<Wallet size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />}
              title={`Minimum order ${formatCents(minimumOrderCents)}`}
              hint={
                <InfoHint
                  title="Minimum order"
                  body={`Your cart has to reach ${formatCents(
                    minimumOrderCents
                  )} before this order can be placed. Checkout will tell you exactly how much more you need.`}
                />
              }
            />
          </>
        )}

        {showAddress && (
          <>
            {(showDelivery || showMinimum) && <Divider />}
            <Row
              icon={<MapPin size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />}
              title="Collect from"
              detail={addressLines.join("\n")}
            />
          </>
        )}
      </View>
      </AccordionSection>
    </View>
  );
}

function Row({
  icon,
  title,
  detail,
  hint,
}: {
  icon: React.ReactNode;
  title: string;
  /** Real content only (e.g. the address). Explanations belong in
   *  `hint`, behind the ⓘ. */
  detail?: string;
  hint?: React.ReactNode;
}) {
  const theme = useTheme();
  return (
    <View style={styles.row}>
      <View style={[styles.iconWrap, { backgroundColor: theme.colors.surfaceVariant }]}>{icon}</View>
      <View style={styles.rowText}>
        <View style={styles.rowTitleLine}>
          <Text style={[styles.rowTitle, { color: theme.colors.onSurface }]}>{title}</Text>
          {hint}
        </View>
        {detail && <Text style={[styles.rowDetail, { color: theme.colors.onSurfaceVariant }]}>{detail}</Text>}
      </View>
    </View>
  );
}

function Divider() {
  const theme = useTheme();
  return <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />;
}

const styles = StyleSheet.create({
  wrap: { paddingHorizontal: spacing.md },
  card: { borderRadius: radius.lg, borderWidth: 1, padding: spacing.md, gap: spacing.md },
  row: { flexDirection: "row", gap: spacing.md, alignItems: "flex-start" },
  iconWrap: { width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center" },
  rowText: { flex: 1, gap: 2 },
  rowTitleLine: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  rowTitle: { ...typography.body, fontWeight: "700" },
  rowDetail: { ...typography.bodySmall, lineHeight: 19 },
  divider: { height: StyleSheet.hairlineWidth, marginLeft: 52 },
});
