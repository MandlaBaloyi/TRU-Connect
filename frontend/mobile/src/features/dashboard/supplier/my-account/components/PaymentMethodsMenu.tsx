import React, { useState } from "react";
import { Pressable, StyleSheet } from "react-native";
import { Menu, useTheme } from "react-native-paper";
import { Info, MoreVertical } from "lucide-react-native";

import { spacing } from "@/theme/spacing";

interface Props {
  onAbout: () => void;
}

/**
 * The Payment methods screen's own "⋮" — same self-contained
 * Menu+anchor-Pressable shape as CartMenu and ProductDetailMenu.
 *
 * WHY THE EXPLANATION MOVED UP HERE. The screen had grown standing
 * grey paragraphs: what direct payment means, what happens if you turn
 * both rails off, how cash and EFT are recorded. Each sentence was
 * individually defensible and together they were most of the screen —
 * exactly the problem InfoHint's own docstring describes, arriving a
 * second time in a different place.
 *
 * So the rows say what the things ARE, this says what they MEAN, and a
 * supplier who already knows never reads either. Anything that needs
 * saying at the moment of a decision is said in that decision's own
 * confirmation dialog instead, where it cannot be scrolled past.
 */
export function PaymentMethodsMenu({ onAbout }: Props) {
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
        title="How payments work"
        leadingIcon={() => <Info size={20} color={theme.colors.onSurface} strokeWidth={2} />}
      />
    </Menu>
  );
}

const styles = StyleSheet.create({
  iconButton: { padding: spacing.xs },
});
