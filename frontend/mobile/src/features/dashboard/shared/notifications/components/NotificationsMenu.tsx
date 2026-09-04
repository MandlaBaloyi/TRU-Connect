import React, { useState } from "react";
import { Pressable, StyleSheet } from "react-native";
import { Menu, useTheme } from "react-native-paper";
import { CheckCheck, MoreVertical } from "lucide-react-native";

import { spacing } from "@/theme/spacing";

interface Props {
  onMarkAllAsRead: () => void;
}

/** The notifications screen's own "⋮" -- one clear action, matching
 *  the same restraint already used on the cart's own menu (a menu
 *  with one genuinely useful item beats one padded with speculative
 *  ones). */
export function NotificationsMenu({ onMarkAllAsRead }: Props) {
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
          onMarkAllAsRead();
        }}
        title="Mark all as read"
        leadingIcon={() => <CheckCheck size={20} color={theme.colors.onSurface} strokeWidth={2} />}
      />
    </Menu>
  );
}

const styles = StyleSheet.create({
  iconButton: { padding: spacing.xs },
});
