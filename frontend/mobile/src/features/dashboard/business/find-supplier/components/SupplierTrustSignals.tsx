import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { CircleCheck, Truck, Users } from "lucide-react-native";

import { InfoHint } from "@/components/ui/InfoHint";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ProfileCard, ProfileSection } from "./ProfileSection";
import type { SupplierTrust } from "../types";

/**
 * The supplier's trading record, as three figures across one row —
 * the followers/following/posts shape every social profile uses.
 *
 * WHY THREE, ACROSS. This started as a stacked list of five bordered
 * rows, which ran nearly a full screen on a phone and pushed the
 * supplier's actual products below the fold. Reported directly as "too
 * long". A stat row reads in one glance, takes a fifth of the height,
 * and is the format people already know how to read.
 *
 * WHICH THREE: businesses connected, orders accepted, orders
 * fulfilled. These are the BRAND-AWARENESS numbers — what a business
 * weighs when deciding whether to deal with a stranger.
 *
 * REPEAT BUYERS USED TO BE THE THIRD, and was removed on purpose.
 * It is a genuinely strong signal, but it is a signal ABOUT the
 * supplier's own performance rather than about their standing: whether
 * buyers come back is the supplier's internal business to act on, not
 * a badge for strangers to read. It moved to the supplier's own
 * TrackRecordPanel, where it sits with the other figures they can
 * actually do something about.
 *
 * ORDERS FULFILLED HOLDS THE THIRD COLUMN WITHOUT A NUMBER. Nothing
 * records that an order reached the business — StockOrderStatus ends
 * at CONFIRMED, with no fulfilled/delivered state and no action that
 * would set one — so there is no honest figure to print. An earlier
 * revision put it as a quiet line under the row instead, reasoning
 * that an empty column costs more than it says. That call was
 * deliberately reversed: the fulfilment model is still being designed,
 * and reserving the column shows the card's real final shape rather
 * than presenting a two-figure card that will have to be re-learned
 * later. It says "coming soon" in the figure's place and explains
 * itself in the section ⓘ. Replace the placeholder — not the layout —
 * the moment fulfilment is recorded.
 *
 * ONE ⓘ FOR THE SECTION, not one per figure. Three info icons in a
 * three-column row is more chrome than content, and social stat rows
 * don't caption individual numbers. The section hint covers all three.
 *
 * EVERY NUMBER IS DERIVED, NOT DECLARED — real connections and real
 * confirmed orders. A supplier cannot type any of them in, and there
 * is nothing to game the way a review score invites. That rule is
 * exactly why the fulfilled column is empty rather than estimated.
 *
 * SILENCE IS THE HONEST ANSWER FOR A NEW SUPPLIER. Each figure hides
 * at zero rather than rendering a nought: "0 orders accepted" reads as
 * a warning about a supplier whose only crime is being new. If neither
 * real figure has anything to say, the whole section disappears —
 * the reserved column alone is not a track record.
 */
export function SupplierTrustSignals({
  businessName,
  connectedBusinessCount,
  trust,
}: {
  /** Closes the card as a quiet brand line under the figures. The
   *  header above already carries the name, but this card is the part
   *  a business screenshots or scrolls back to, and a bare grid of
   *  numbers detached from whose numbers they are is weaker for it. */
  businessName: string;
  connectedBusinessCount: number;
  /** Null when the supplier switched their track record off — the whole
   *  section disappears rather than showing a stripped-down version,
   *  which would invite "what are they hiding". */
  trust: SupplierTrust | null;
}) {
  const theme = useTheme();
  if (!trust) return null;

  /** `figure: null` renders the reserved-column placeholder instead of
   *  a number — see the "orders fulfilled" note in this file's own
   *  docstring. */
  const stats: { icon: React.ReactNode; figure: number | null; label: string }[] = [];

  if (connectedBusinessCount > 0) {
    stats.push({
      icon: <Users size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />,
      figure: connectedBusinessCount,
      // "connected", never "buy from them": this counts CONNECTIONS,
      // and a business can be connected without ever having ordered.
      label: connectedBusinessCount === 1 ? "business\nconnected" : "businesses\nconnected",
    });
  }

  if (trust.acceptedOrderCount > 0) {
    stats.push({
      icon: <CircleCheck size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />,
      figure: trust.acceptedOrderCount,
      label: trust.acceptedOrderCount === 1 ? "order\naccepted" : "orders\naccepted",
    });
  }

  // NOTHING REAL YET, AND NOT HIDDEN AT ZERO EITHER. The two figures
  // above disappear when they have nothing to say; this one has
  // nothing to say by construction, for every supplier, so hiding it
  // would just mean nobody ever sees the shape the card is heading
  // for. It shows only alongside a real figure (see the guard below).
  const fulfilled = {
    icon: <Truck size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />,
    figure: null,
    label: "orders\nfulfilled",
  };

  // A card holding ONLY the placeholder is not a track record -- it is
  // an empty promise with a border around it. New suppliers get the
  // section omitted entirely, exactly as before.
  if (stats.length === 0) return null;
  stats.push(fulfilled);

  return (
    <ProfileSection
      label="Track record"
      accessory={
        <InfoHint
          title="Track record"
          body={[
            "Built from what has actually happened on TruConnect — real connections and real accepted orders. None of it is self-reported, and none of it can be typed in.",
            "Businesses connected: they can order from this supplier. It doesn't by itself mean they have.",
            "Orders accepted: orders this supplier took on, all time.",
            "Orders fulfilled: how many orders actually reached the business. TruConnect can't measure this yet — nothing records delivery, so there would be no honest number to show. The column is kept empty rather than filled with a guess.",
          ]}
        />
      }
    >
      <ProfileCard>
        <View style={styles.row}>
          {stats.map((stat, index) => (
            <React.Fragment key={stat.label}>
              {index > 0 && (
                <View style={[styles.columnRule, { backgroundColor: theme.colors.outlineVariant }]} />
              )}
              <View style={[styles.stat, stat.figure === null && styles.statReserved]}>
                {stat.icon}
                {stat.figure === null ? (
                  // "Coming soon" WHERE THE NUMBER GOES, at the
                  // number's size, so the column reads as a figure
                  // that isn't ready rather than a figure of zero.
                  // An em-dash here would look like a real measurement
                  // that came back empty.
                  <Text style={[styles.comingSoon, { color: theme.colors.onSurfaceVariant }]}>Coming{"\n"}soon</Text>
                ) : (
                  <Text style={[styles.figure, { color: theme.colors.onSurface }]}>
                    {stat.figure.toLocaleString()}
                  </Text>
                )}
                <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>{stat.label}</Text>
              </View>
            </React.Fragment>
          ))}
        </View>

        {/* WHOSE NUMBERS THESE ARE. The brand header carries the name
            too, but this card is the part a business scrolls back to
            and screenshots, and a bare grid of figures detached from
            the business they belong to is weaker for it. */}
        <View style={[styles.nameRule, { backgroundColor: theme.colors.outlineVariant }]} />
        <Text style={[styles.nameLine, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
          {businessName}
        </Text>
      </ProfileCard>
    </ProfileSection>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "flex-start", paddingVertical: spacing.md },
  stat: { flex: 1, alignItems: "center", gap: 3, paddingHorizontal: spacing.xs },
  figure: { ...typography.h1, fontWeight: "800", fontSize: 22, lineHeight: 26 },
  label: { ...typography.bodySmall, fontSize: 11, lineHeight: 14, textAlign: "center" },
  columnRule: { width: StyleSheet.hairlineWidth, alignSelf: "stretch", marginVertical: 2 },
  // Quieter than the two real columns, so the eye lands on the figures
  // that mean something first and reads the reserved one second.
  statReserved: { opacity: 0.55 },
  comingSoon: { ...typography.bodySmall, fontSize: 11, lineHeight: 13, fontWeight: "700", textAlign: "center" },
  nameRule: { height: StyleSheet.hairlineWidth },
  nameLine: {
    ...typography.bodySmall,
    fontSize: 12,
    fontWeight: "600",
    textAlign: "center",
    paddingVertical: spacing.sm,
  },
});
