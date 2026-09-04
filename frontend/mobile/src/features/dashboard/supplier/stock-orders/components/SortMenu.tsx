import React, { useState } from "react";
import { Pressable, StyleSheet } from "react-native";
import { Menu, useTheme } from "react-native-paper";
import { ArrowDownWideNarrow, ArrowUpNarrowWide, Check, MoreVertical } from "lucide-react-native";

import { spacing } from "@/theme/spacing";

import type { SortOrder } from "../types";

interface Props {
  sortOrder: SortOrder;
  onChange: (order: SortOrder) => void;
}

/** The Stock Orders screen's own real "⋮" -- confirmed directly:
 *  bulk-approving or bulk-declining shouldn't exist (every order
 *  deserves its own real decision), so sort is genuinely the one
 *  thing worth putting here for now, not a menu padded with
 *  speculative items. */
export function SortMenu({ sortOrder, onChange }: Props) {
  const theme = useTheme();
  const [visible, setVisible] = useState(false);

  const select = (order: SortOrder) => {
    setVisible(false);
    onChange(order);
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
          accessibilityLabel="Sort"
        >
          <MoreVertical size={20} color={theme.colors.onSurface} strokeWidth={2.4} />
        </Pressable>
      }
    >
      <Menu.Item
        onPress={() => select("NEWEST")}
        title="Newest first"
        leadingIcon={() => <ArrowDownWideNarrow size={20} color={theme.colors.onSurface} strokeWidth={2} />}
        trailingIcon={sortOrder === "NEWEST" ? () => <Check size={18} color={theme.colors.primary} strokeWidth={2.4} /> : undefined}
      />
      <Menu.Item
        onPress={() => select("OLDEST")}
        title="Oldest first"
        leadingIcon={() => <ArrowUpNarrowWide size={20} color={theme.colors.onSurface} strokeWidth={2} />}
        trailingIcon={sortOrder === "OLDEST" ? () => <Check size={18} color={theme.colors.primary} strokeWidth={2.4} /> : undefined}
      />
    </Menu>
  );
}

const styles = StyleSheet.create({
  iconButton: { padding: spacing.xs },
});
