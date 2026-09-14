import React from "react";
import { BadgeCheck } from "lucide-react-native";
import { useTheme } from "react-native-paper";

/**
 * The verified tick. ONE colour, one icon, one size scale.
 *
 * WHY THIS EXISTS: the tick had drifted to three different treatments
 * -- blue on the supplier card and the header title, green on the
 * brand header and the verification badge, white-on-green on the
 * avatar. A trust mark that changes colour between screens is not a
 * trust mark; the reader cannot tell whether the two ticks mean the
 * same thing, which is the only thing a tick has to communicate.
 *
 * GREEN, NOT BLUE, and the app had already half-decided this. On the
 * profile avatar the verified dot is green while the camera button
 * beside it is blue -- so in this design blue is what you can DO and
 * green is what has been CHECKED. A blue tick would also collide with
 * the blue used for links, prices and the "N businesses bought this"
 * line, which is the one place on a card competing for the same
 * attention.
 *
 * (Blue is the convention elsewhere on the internet. It loses here
 * because internal consistency beats an external convention that this
 * app's own palette already contradicts.)
 *
 * PUT IT BESIDE THE NAME, not on the photo. A tick on an avatar is
 * ambiguous about what it certifies -- the picture, or the business --
 * and it gets clipped by every circular crop. The avatar's own badge
 * dot is a different component for a different job: a glance-level
 * marker where no name is shown.
 *
 * WHETHER to show it is decided in ONE other place, config's
 * showsAsVerified. This file only decides how it looks.
 */
export function VerifiedTick({ size = 14 }: { size?: number }) {
  const theme = useTheme();
  return (
    <BadgeCheck
      size={size}
      color={theme.colors.secondary}
      strokeWidth={2.4}
      accessibilityLabel="Verified"
    />
  );
}
