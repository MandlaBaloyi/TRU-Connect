import React from "react";
import { Button, ButtonProps } from "react-native-paper";
import { StyleSheet } from "react-native";

/**
 * Primary Button - solid fill, used for the single most important action
 * on a screen. Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 8.
 */
export function PrimaryButton({ children, style, ...rest }: ButtonProps) {
  return (
    <Button mode="contained" style={[styles.button, style]} contentStyle={styles.content} {...rest}>
      {children}
    </Button>
  );
}

const styles = StyleSheet.create({
  button: { borderRadius: 12 },
  content: { height: 52 },
});
