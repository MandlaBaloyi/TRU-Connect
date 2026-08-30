import React, { useState } from "react";
import { Pressable, StyleSheet } from "react-native";
import { Menu, useTheme } from "react-native-paper";
import { MoreVertical, UserX } from "lucide-react-native";

import { spacing } from "@/theme/spacing";

interface Props {
  onViewDisconnectedSuppliers: () => void;
}

/** The Community tab's own "⋮" -- was purely decorative before (icon
 *  rendered, no handler at all). Same self-contained
 *  Menu+anchor-Pressable shape as
 *  my-suppliers/components/SupplierCatalogMenu.tsx, passed as
 *  AppHeader's own rightIcon (with onRightIconPress left undefined) --
 *  AppHeader always wraps rightIcon in its own outer Pressable
 *  regardless, but with no onPress supplied that outer wrapper is
 *  inert; the actual open/close is handled by this component's own
 *  inner anchor Pressable, nested inside it. */
export function CommunityOverflowMenu({ onViewDisconnectedSuppliers }: Props) {
  const theme = useTheme();
  const [visible, setVisible] = useState(false);

  const runAndClose = (action: () => void) => {
    setVisible(false);
    action();
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
        onPress={() => runAndClose(onViewDisconnectedSuppliers)}
        title="Disconnected Suppliers"
        leadingIcon={({ size, color }) => <UserX size={size} color={color} strokeWidth={2} />}
      />
    </Menu>
  );
}

const styles = StyleSheet.create({
  iconButton: { padding: spacing.xs, marginLeft: spacing.xs },
});
