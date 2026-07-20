import React from "react";
import { Button, ButtonProps } from "react-native-paper";
import { StyleSheet } from "react-native";

/**
 * Secondary Button - outlined, used for supporting actions.
 * Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 8.
 */
export function SecondaryButton({ children, style, ...rest }: ButtonProps) {
  return (
    <Button mode="outlined" style={[styles.button, style]} contentStyle={styles.content} {...rest}>
      {children}
    </Button>
  );
}

const styles = StyleSheet.create({
  button: { borderRadius: 12 },
  content: { height: 52 },
});
