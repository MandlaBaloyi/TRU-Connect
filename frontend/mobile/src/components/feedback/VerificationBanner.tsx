import React, { useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { Text } from "react-native-paper";
import { ChevronDown, ChevronUp, EyeOff } from "lucide-react-native";

import { useVerificationStatus } from "@/features/dashboard/supplier/verification/hooks/useVerificationStatus";
import { palette } from "@/theme/colors";
import { spacing } from "@/theme/spacing";

/**
 * "Your shop is ready — buyers cannot see it yet."
 *
 * THE CURTAIN, EXPLAINED TO THE PERSON BEHIND IT. A supplier can build
 * their entire catalogue before verification and no business can find
 * them (V2_12 Phase 1). Without this banner that state is invisible
 * from inside the app: a supplier would upload three hundred products,
 * receive no orders, and have no way to know whether the platform was
 * broken, the market was quiet, or they had done something wrong.
 *
 * IT IS NOT DISMISSIBLE, and that is a deliberate choice rather than an
 * oversight. A dismissible banner is one a supplier closes on day one
 * and never sees again, which returns them to exactly the confusion it
 * exists to prevent. It collapses instead -- the headline always
 * visible, the explanation one tap away -- so it stops taking space
 * without ever stopping telling the truth.
 *
 * THE TONE IS THE FEATURE. V2_03 Part 4.5 is explicit: the message is
 * "your shop is ready and nobody can see it yet", never "you are not
 * verified". The second reads as a scolding to somebody who has just
 * spent an hour building a catalogue, and it is also less accurate --
 * their work is real; it is the visibility that is pending. Hence the
 * neutral slate colour rather than the danger red OfflineBanner uses:
 * nothing is wrong, something is simply not finished.
 *
 * The words themselves come from the SERVER, not from this file, so
 * they can be changed without an app release.
 */
export function VerificationBanner() {
  const { data } = useVerificationStatus();
  const [expanded, setExpanded] = useState(false);

  // RENDERS NOTHING WHILE LOADING, and nothing once verified. A banner
  // that flashes on every cold start for suppliers who are already
  // live would be a bug, not a reminder.
  if (!data || data.visibleToBuyers) return null;

  const Chevron = expanded ? ChevronUp : ChevronDown;

  return (
    <Pressable
      onPress={() => setExpanded((open) => !open)}
      accessibilityRole="button"
      accessibilityLabel={data.headline}
      accessibilityHint={
        expanded ? "Collapses the explanation" : "Expands to explain what happens next"
      }
      style={styles.banner}
    >
      <View style={styles.row}>
        <EyeOff size={16} color={palette.white} />
        <Text style={styles.headline} numberOfLines={expanded ? undefined : 2}>
          {data.headline}
        </Text>
        <Chevron size={16} color={palette.white} />
      </View>
      {expanded ? <Text style={styles.detail}>{data.detail}</Text> : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  banner: {
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.md,
    // NOT palette.danger. OfflineBanner is red because being offline is
    // a fault; waiting for verification is not -- so this is brand
    // blue, which reads as information rather than as an alarm.
    backgroundColor: palette.truePointBlueLight,
  },
  row: { flexDirection: "row", alignItems: "center", gap: 8 },
  headline: { flex: 1, color: palette.white, fontSize: 12, fontWeight: "600" },
  detail: {
    color: palette.white,
    fontSize: 12,
    lineHeight: 17,
    opacity: 0.9,
    marginTop: spacing.xs,
  },
});
