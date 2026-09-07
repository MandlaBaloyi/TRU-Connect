import React, { useState } from "react";
import { Pressable, StyleSheet } from "react-native";
import { Menu, useTheme } from "react-native-paper";
import { MoreVertical } from "lucide-react-native";

import { spacing } from "@/theme/spacing";

export interface CommunityMenuItem {
  key: string;
  title: string;
  /** Rendered via Paper's own leadingIcon contract, so the menu
   *  supplies size/colour and the caller only picks the glyph. */
  icon: (props: { size: number; color: string }) => React.ReactNode;
  onPress: () => void;
}

interface Props {
  items: CommunityMenuItem[];
}

/** The Community tab's own "⋮" -- was purely decorative before (icon
 *  rendered, no handler at all). Same self-contained
 *  Menu+anchor-Pressable shape as
 *  my-suppliers/components/SupplierCatalogMenu.tsx, passed as
 *  AppHeader's own rightIcon (with onRightIconPress left undefined) --
 *  AppHeader always wraps rightIcon in its own outer Pressable
 *  regardless, but with no onPress supplied that outer wrapper is
 *  inert; the actual open/close is handled by this component's own
 *  inner anchor Pressable, nested inside it.
 *
 *  ITEMS ARE PASSED IN rather than hardcoded. This started as the
 *  business menu with one fixed "Disconnected Suppliers" entry, which
 *  was fine while only one role reached it. The supplier side now uses
 *  the same "⋮" for a completely different set (its visibility
 *  settings), and it has no disconnected-connections screen at all --
 *  so a role flag would have meant this shared component knowing about
 *  both roles' routes. The caller owns its own entries instead; this
 *  file owns only the anchor, the open/close and the close-then-act
 *  ordering. */
export function CommunityOverflowMenu({ items }: Props) {
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
      {items.map((item) => (
        <Menu.Item
          key={item.key}
          onPress={() => runAndClose(item.onPress)}
          title={item.title}
          leadingIcon={({ size, color }) => item.icon({ size, color })}
        />
      ))}
    </Menu>
  );
}

const styles = StyleSheet.create({
  iconButton: { padding: spacing.xs, marginLeft: spacing.xs },
});
