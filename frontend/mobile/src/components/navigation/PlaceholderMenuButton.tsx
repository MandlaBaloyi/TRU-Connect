import React from "react";
import { Alert, Pressable, StyleSheet } from "react-native";
import { useTheme } from "react-native-paper";
import { MoreVertical } from "lucide-react-native";

import { spacing } from "@/theme/spacing";

/**
 * A real, visible 3-dot icon for a header's own rightSlot -- shown
 * now, deliberately not wired to a real menu yet. Confirmed directly:
 * several existing feature headers (Loan Book, Order Book, and
 * others as they come up) never had this icon at all; adding it now
 * as a real, tappable placeholder ("Coming soon") rather than leaving
 * it absent makes the design consistent everywhere immediately, while
 * the real menu contents get decided and wired feature by feature,
 * later.
 */
export function PlaceholderMenuButton() {
  const theme = useTheme();

  return (
    <Pressable
      onPress={() => Alert.alert("Coming soon", "More options for this screen are on the way.")}
      hitSlop={10}
      style={styles.iconButton}
      accessibilityRole="button"
      accessibilityLabel="More options"
    >
      <MoreVertical size={20} color={theme.colors.onSurface} strokeWidth={2.4} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  iconButton: { padding: spacing.xs },
});
