import React, { useState } from "react";
import { Pressable, StyleSheet } from "react-native";
import { Menu, useTheme } from "react-native-paper";
import { Info, MoreVertical } from "lucide-react-native";

import { spacing } from "@/theme/spacing";

interface Props {
  onAbout: () => void;
}

/**
 * The ⋮ in the supplier brand profile's header. Mirrors
 * my-suppliers/components/SupplierCatalogMenu.tsx exactly (same paper
 * Menu, same anchor sizing, own open/closed state). One item for now
 * -- "About connections" -- so the screen leads with brand + products
 * and the connection explainer lives a tap away. Report is a trivial
 * later add here.
 */
export function SupplierProfileMenu({ onAbout }: Props) {
  const theme = useTheme();
  const [visible, setVisible] = useState(false);

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
        onPress={() => {
          setVisible(false);
          onAbout();
        }}
        title="About connections"
        leadingIcon={({ size, color }) => <Info size={size} color={color} strokeWidth={2} />}
      />
    </Menu>
  );
}

const styles = StyleSheet.create({
  iconButton: { padding: spacing.xs, marginLeft: spacing.xs },
});
