import React, { useState } from "react";
import { Pressable, StyleSheet } from "react-native";
import { Menu, useTheme } from "react-native-paper";
import { MoreVertical, TriangleAlert } from "lucide-react-native";

import { spacing } from "@/theme/spacing";

interface Props {
  onReport: () => void;
}

/** The product detail screen's own "⋮" -- deliberately its own small
 *  component rather than inlined in the screen, matching the same
 *  self-contained Menu+anchor-Pressable shape as
 *  SupplierCatalogMenu.tsx (the catalog screen's own 4-item version)
 *  and CommunityOverflowMenu.tsx. Just one item today -- "Report this
 *  product" -- but kept as its own component so a future addition
 *  here doesn't mean restructuring the screen file itself. */
export function ProductDetailMenu({ onReport }: Props) {
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
          onReport();
        }}
        title="Report this product"
        titleStyle={{ color: theme.colors.error }}
        leadingIcon={() => <TriangleAlert size={20} color={theme.colors.error} strokeWidth={2} />}
      />
    </Menu>
  );
}

const styles = StyleSheet.create({
  iconButton: { padding: spacing.xs, marginLeft: spacing.xs },
});
