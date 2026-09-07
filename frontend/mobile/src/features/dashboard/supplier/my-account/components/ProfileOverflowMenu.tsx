import React, { useState } from "react";
import { Pressable, StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import { Menu, useTheme } from "react-native-paper";
import { Eye, MoreVertical, QrCode, Users } from "lucide-react-native";

import { spacing } from "@/theme/spacing";

/**
 * The supplier's own Profile "⋮".
 *
 * WHAT IT DELIBERATELY DOES NOT CONTAIN:
 *
 *   Settings — universal, reachable from More on both roles. A
 *   shortcut to the thing that already has a permanent home spends the
 *   menu on nothing. (Same call as the Community tab's own ⋮.)
 *
 *   Edit / Remove photo — tapping the photo already opens an action
 *   sheet with exactly those. A second path to the same two actions is
 *   a duplicate control, not a convenience.
 *
 *   Deactivate / Delete account — real screens, but they live under My
 *   Account where account lifecycle belongs. A destructive action one
 *   tap from a profile edit screen is a misplacement, not a shortcut.
 *
 * WHAT IT CONTAINS, and why each earns its slot:
 *
 *   My QR code — the one thing a supplier standing on their own
 *   profile most plausibly wants next: hand this to a business so they
 *   can connect. It also exists as an icon on the My Account landing;
 *   that is a second entry point to one destination, not two controls
 *   for one value.
 *
 *   Supplier visibility / Community activity — the switches that used
 *   to be ON this screen. The profile holds the values, Settings holds
 *   who sees them (see ProfileScreen's own docstring), and these two
 *   rows are what keeps that split navigable rather than merely
 *   correct.
 *
 * STILL MISSING, and worth building: "View as a business sees you".
 * The public profile endpoint is @role_required("business"), so a
 * supplier cannot currently fetch their own public view — that is a
 * backend change, not a frontend one, which is the only reason it is
 * not in this list.
 */
export function ProfileOverflowMenu() {
  const theme = useTheme();
  const router = useRouter();
  const [visible, setVisible] = useState(false);

  const go = (path: string) => () => {
    setVisible(false);
    router.push(path as any);
  };

  return (
    <Menu
      visible={visible}
      onDismiss={() => setVisible(false)}
      anchor={
        <Pressable
          onPress={() => setVisible(true)}
          hitSlop={10}
          style={styles.iconButton}
          accessibilityRole="button"
          accessibilityLabel="More options"
        >
          <MoreVertical size={20} color={theme.colors.onSurface} strokeWidth={2.4} />
        </Pressable>
      }
    >
      <Menu.Item
        onPress={go("/supplier/my-account/qr-code")}
        title="My QR code"
        leadingIcon={({ size, color }) => <QrCode size={size} color={color} strokeWidth={2} />}
      />
      <Menu.Item
        onPress={go("/supplier/settings/supplier-visibility")}
        title="Supplier visibility"
        leadingIcon={({ size, color }) => <Eye size={size} color={color} strokeWidth={2} />}
      />
      <Menu.Item
        onPress={go("/supplier/settings/community-activity")}
        title="Community activity"
        leadingIcon={({ size, color }) => <Users size={size} color={color} strokeWidth={2} />}
      />
    </Menu>
  );
}

const styles = StyleSheet.create({
  iconButton: { padding: spacing.xs, marginLeft: spacing.xs },
});
