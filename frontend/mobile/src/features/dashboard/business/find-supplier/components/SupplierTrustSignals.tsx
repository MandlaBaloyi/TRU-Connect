import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { CircleCheck, Package, Repeat, Truck, Users } from "lucide-react-native";

import { InfoHint } from "@/components/ui/InfoHint";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ProfileCard, ProfileSection } from "./ProfileSection";
import type { SupplierTrust } from "../types";

/**
 * The three things an informal business actually weighs before sending
 * money to a supplier it has never traded with: do OTHER businesses buy
 * here, do orders go through, and how fast do they answer.
 *
 * EVERY NUMBER HERE IS DERIVED, NOT DECLARED. Connections, acceptance
 * rate and response time all come from what has genuinely happened on
 * the platform — a supplier cannot type any of them in, and there is
 * nothing to game the way a review score invites. That's the whole
 * reason these carry weight where the supplier's own description
 * doesn't.
 *
 * A HEADLINE FIGURE PER ROW, not a sentence. These first shipped as
 * three stacked grey pills, each holding a full sentence — which read
 * as three lines of small print rather than three facts, and made the
 * most important number on the profile ("2 businesses connected")
 * the same visual weight as its own caption. Now each row leads with
 * the FIGURE, big and dark, with the label beneath it in muted text:
 * the numbers are what a business scans for, so the numbers are what
 * the eye lands on.
 *
 * COUNTS, NEVER RATES. This first shipped as
 * "accepted X of their last Y orders" plus a median reply time, and
 * both were removed: the ratio led with a new supplier's failures
 * ("accepted 0 of 1"), and the median actively ignored improvement --
 * a supplier who answered the next order in minutes saw the number not
 * move at all, which reads as broken even though it's correct
 * statistics. A count moves the moment they accept something.
 *
 * (It is not strictly monotonic: a supplier who cancels an order they
 * had already confirmed loses that credit, which is correct -- an order
 * pulled out of was not fulfilled. See the backend repository's note.)
 *
 * SILENCE IS THE HONEST ANSWER FOR A NEW SUPPLIER. Every figure hides
 * at zero rather than rendering a nought — "0 accepted orders" reads as
 * a warning about a supplier whose only crime is being new. A supplier
 * with no history simply shows fewer signals; they are never shown a
 * bad one they didn't earn. There is no minimum-sample gate anymore,
 * and none is needed: a COUNT of one is a small true fact, where a RATE
 * over one order was misleading.
 */
export function SupplierTrustSignals({
  connectedBusinessCount,
  trust,
}: {
  connectedBusinessCount: number;
  /** Null when the supplier switched their track record off — the whole
   *  section disappears rather than showing a stripped-down version,
   *  which would invite "what are they hiding". */
  trust: SupplierTrust | null;
}) {
  if (!trust) return null;
  return <TrackRecord connectedBusinessCount={connectedBusinessCount} trust={trust} />;
}

function TrackRecord({
  connectedBusinessCount,
  trust,
}: {
  connectedBusinessCount: number;
  trust: SupplierTrust;
}) {
  const theme = useTheme();

  const rows: { icon: React.ReactNode; figure: string; label: string; hint: string }[] = [];

  if (connectedBusinessCount > 0) {
    rows.push({
      icon: <Users size={17} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />,
      figure: connectedBusinessCount.toLocaleString(),
      // "buy from them" was WRONG: this counts active CONNECTIONS, and
      // a business can be connected without ever having ordered
      // anything. The row directly beneath it ("orders accepted") is
      // the one that reports actual buying -- claiming both from one
      // number made the connection count look like sales.
      label: connectedBusinessCount === 1 ? "business connected" : "businesses connected",
      hint: "Businesses currently connected to this supplier on TruConnect. A connection means they can order — it doesn't by itself mean they have. Real, active connections only; not followers or views.",
    });
  }

  if (trust.acceptedOrderCount > 0) {
    rows.push({
      icon: <CircleCheck size={17} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />,
      figure: trust.acceptedOrderCount.toLocaleString(),
      label: trust.acceptedOrderCount === 1 ? "order accepted" : "orders accepted",
      hint: "How many orders this supplier has accepted on TruConnect, all time. It goes up each time they accept another one, and it isn't something they can type in. If they later cancel an order they'd confirmed, it stops counting.",
    });
  }

  if (trust.repeatBusinessCount > 0) {
    rows.push({
      icon: <Repeat size={17} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />,
      figure: trust.repeatBusinessCount.toLocaleString(),
      label: trust.repeatBusinessCount === 1 ? "business ordered again" : "businesses ordered again",
      hint: "Businesses that had more than one order accepted by this supplier. Coming back is the strongest signal there is — it's a verdict on the first order, and nobody can fake it.",
    });
  }

  if (trust.unitsSoldCount > 0) {
    rows.push({
      icon: <Package size={17} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />,
      figure: trust.unitsSoldCount.toLocaleString(),
      label: trust.unitsSoldCount === 1 ? "unit sold" : "units sold",
      hint: "Total items this supplier has sold through accepted orders. Order count alone hides volume — sixteen orders of one case and sixteen of forty are very different suppliers.",
    });
  }

  if (rows.length === 0) return null;

  return (
    <ProfileSection label="Track record">
      <ProfileCard>
        {rows.map((row, index) => (
          <View key={row.label}>
            {index > 0 && <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />}
            <View style={styles.row}>
              <View style={[styles.iconWrap, { backgroundColor: theme.colors.surfaceVariant }]}>{row.icon}</View>
              <View style={styles.text}>
                <Text style={[styles.figure, { color: theme.colors.onSurface }]}>{row.figure}</Text>
                <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>{row.label}</Text>
              </View>
              <InfoHint title={row.label} body={row.hint} size={15} />
            </View>
          </View>
        ))}

        {/* A REAL SLOT FOR A FEATURE THAT DOESN'T EXIST YET. Nothing
            anywhere records that an order was actually delivered --
            neither side can confirm receipt -- so this cannot be
            computed today. Shown greyed and labelled rather than
            silently omitted: a business scanning a track record should
            know that "fulfilled" is a thing TruConnect will measure,
            and a supplier should know it's coming. Replace the whole
            row the moment delivery confirmation is real. */}
        <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />
        <View style={[styles.row, styles.pending]}>
          <View style={[styles.iconWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
            <Truck size={17} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />
          </View>
          <View style={styles.text}>
            <Text style={[styles.figure, { color: theme.colors.onSurfaceVariant }]}>—</Text>
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>
              orders fulfilled · coming soon
            </Text>
          </View>
          <InfoHint
            title="Orders fulfilled"
            body="How many orders actually reached the business. TruConnect can't measure this yet — nothing records delivery, so there'd be no honest number to show. It's coming; until then this row stays empty rather than guessing."
            size={15}
          />
        </View>
      </ProfileCard>
    </ProfileSection>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: spacing.md, padding: spacing.md },
  iconWrap: { width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center" },
  text: { flex: 1 },
  figure: { ...typography.body, fontWeight: "800", fontSize: 17 },
  label: { ...typography.bodySmall, fontSize: 12, marginTop: 1 },
  divider: { height: StyleSheet.hairlineWidth, marginLeft: 52 },
  pending: { opacity: 0.55 },
});
