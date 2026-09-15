import React from "react";
import {
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type TextStyle,
  type ViewStyle,
} from "react-native";

import { showsAsVerified } from "@/constants/config";
import { VerifiedTick } from "@/components/ui/VerifiedTick";
import { spacing } from "@/theme/spacing";

/**
 * A supplier's business name, with its verification tick attached.
 *
 * THE POINT IS THAT THE TWO CANNOT BE SEPARATED. The tick used to
 * appear on three screens out of a dozen that print a supplier's name,
 * so whether a business saw it depended on which route they took to the
 * same supplier -- and a trust mark that is present on the search
 * result and absent in the cart is worse than one that is never shown,
 * because its absence reads as a statement.
 *
 * WHY THIS IS NOT DECORATION, which was my first reading and was wrong.
 * The verification curtain hides an unverified supplier from SEARCH and
 * from NEW commerce, so on any discovery surface every supplier is
 * verified by construction and a tick really does say nothing. But the
 * curtain deliberately does NOT cover established relationships --
 * verification/visibility.py: "revoking a supplier must not rewrite
 * trade that really happened" -- so My Connections, an open cart, the
 * checkout screen and an existing order CAN show a supplier whose
 * verification was revoked after the relationship began.
 *
 * Those are the screens that had no tick. Which means the ABSENCE of
 * one is the real signal, and it was missing from exactly the places it
 * would have meant something.
 *
 * NULL STATUS SHOWS NO TICK, and that is deliberate rather than a
 * fallback: a payload that has not been taught to send the status must
 * not silently claim a supplier is verified. Adding the field to a new
 * endpoint is what turns the tick on there, which keeps the claim tied
 * to real data instead of to a component's default.
 */
export function SupplierName({
  name,
  verificationStatus,
  style,
  containerStyle,
  numberOfLines = 1,
  tickSize = 13,
}: {
  name: string;
  /** From the API. Undefined/null means "this payload does not say",
   *  which renders no tick -- never an assumed one. */
  verificationStatus?: string | null;
  style?: StyleProp<TextStyle>;
  /** For layouts that are not left-aligned rows -- the "Your
   *  suppliers" tile centres a two-line name under a round avatar. */
  containerStyle?: StyleProp<ViewStyle>;
  numberOfLines?: number;
  tickSize?: number;
}) {
  const verified = showsAsVerified(verificationStatus);

  // No tick: render a bare Text so this drops into any existing layout
  // that was already styling a plain name, with no wrapper to fight.
  if (!verified) {
    return (
      <Text style={style} numberOfLines={numberOfLines}>
        {name}
      </Text>
    );
  }

  return (
    <View style={[styles.row, containerStyle]}>
      <Text style={[style, styles.name]} numberOfLines={numberOfLines}>
        {name}
      </Text>
      <VerifiedTick size={tickSize} />
    </View>
  );
}

const styles = StyleSheet.create({
  // gap 3, NOT spacing.xs (4). The tick is not a sibling of the name,
  // it is PART of it -- at 4px on an 11px caption it read as a separate
  // little symbol sitting nearby rather than as a mark on the business.
  row: { flexDirection: "row", alignItems: "center", gap: 3, flexShrink: 1 },
  // flexShrink so a long business name truncates rather than pushing
  // the tick off the edge -- the tick is the part that must survive.
  name: { flexShrink: 1 },
});
