import React from "react";
import { Alert, Pressable, StyleSheet, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Heart, MessagesSquare, Share2 } from "lucide-react-native";

import { spacing } from "@/theme/spacing";

/**
 * Like / comment / share, on a product card.
 *
 * EXTRACTED so the brand profile's showcase strips and the stock
 * catalogue's grid share ONE implementation. They had drifted: the
 * catalogue grew these three actions, the showcase never did, so the
 * same product looked like a different kind of object depending on
 * which screen you found it on. Reported directly.
 *
 * (The showcase lives in find-supplier and the catalogue card in
 * my-suppliers, and my-suppliers depends on find-supplier rather than
 * the reverse — so this sits in components/, neutral ground, the same
 * reasoning as services/contact/contactLinks.ts.)
 *
 * NOT YET FUNCTIONAL, AND HONEST ABOUT IT. Each action opens a real
 * "Coming soon" alert rather than doing nothing: a control that
 * silently no-ops reads as broken, which is worse than one that says
 * it isn't ready. This is also this codebase's existing rule — see
 * SwitchCard's own note against controls that look functional when
 * they aren't. When likes/comments/sharing become real, the handlers
 * swap here once and both screens get them.
 */
export function ProductActionsRow({
  productName,
  size = 20,
  onLike,
  onComment,
  onShare,
}: {
  productName: string;
  size?: number;
  /** Real handlers, when they exist. Omitted -> the "Coming soon"
   *  placeholder, which is the current state for all three. */
  onLike?: () => void;
  onComment?: () => void;
  onShare?: () => void;
}) {
  const theme = useTheme();

  const comingSoon = (feature: string) =>
    Alert.alert("Coming soon", `${feature} isn't available yet, but it's on the way.`);

  const actions = [
    { icon: Heart, label: `Like ${productName}`, onPress: onLike ?? (() => comingSoon("Likes")) },
    { icon: MessagesSquare, label: `Comment on ${productName}`, onPress: onComment ?? (() => comingSoon("Comments")) },
    { icon: Share2, label: `Share ${productName}`, onPress: onShare ?? (() => comingSoon("Sharing")) },
  ];

  return (
    <View style={styles.row}>
      {actions.map(({ icon: Icon, label, onPress }) => (
        <Pressable
          key={label}
          // stopPropagation: these sit INSIDE a card that is itself
          // pressable (it opens the product), so without this a tap on
          // Share would also navigate.
          onPress={(event) => {
            event.stopPropagation();
            onPress();
          }}
          hitSlop={8}
          style={styles.button}
          accessibilityRole="button"
          accessibilityLabel={label}
        >
          <Icon size={size} color={theme.colors.onSurfaceVariant} strokeWidth={2.5} />
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingTop: spacing.xs },
  button: { paddingVertical: 2 },
});
