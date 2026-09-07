import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Minus, Plus } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * − qty + , for choosing how many before adding to a cart.
 *
 * WHY THIS EXISTS AT ALL: every Add to Cart in this app added exactly
 * ONE, and a business buying stock then had to open the cart and press
 * + nine more times. That's fine for consumer retail, where you buy one
 * of a thing; it's the wrong default for wholesale, where a spaza owner
 * buys ten cases and one is the unusual case.
 *
 * CLAMPED, NOT VALIDATED. There's no text input and no way to type a
 * number, so the value can never be empty, negative, fractional, or a
 * string — the component simply cannot produce an invalid quantity, and
 * no caller has to check for one.
 */
export function QuantityStepper({
  value,
  onChange,
  min = 1,
  max = 999,
  disabled = false,
}: {
  value: number;
  onChange: (next: number) => void;
  min?: number;
  max?: number;
  disabled?: boolean;
}) {
  const theme = useTheme();

  const step = (delta: number) => {
    const next = Math.min(max, Math.max(min, value + delta));
    if (next !== value) onChange(next);
  };

  return (
    <View style={[styles.wrap, { borderColor: theme.colors.outline, opacity: disabled ? 0.5 : 1 }]}>
      <StepButton
        icon={<Minus size={16} color={theme.colors.onSurface} strokeWidth={2.6} />}
        label="Decrease quantity"
        onPress={() => step(-1)}
        disabled={disabled || value <= min}
      />
      <Text style={[styles.value, { color: theme.colors.onSurface }]}>{value}</Text>
      <StepButton
        icon={<Plus size={16} color={theme.colors.onSurface} strokeWidth={2.6} />}
        label="Increase quantity"
        onPress={() => step(1)}
        disabled={disabled || value >= max}
      />
    </View>
  );
}

function StepButton({
  icon,
  label,
  onPress,
  disabled,
}: {
  icon: React.ReactNode;
  label: string;
  onPress: () => void;
  disabled: boolean;
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      hitSlop={6}
      style={({ pressed }) => [styles.button, { opacity: disabled ? 0.35 : pressed ? 0.6 : 1 }]}
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled }}
    >
      {icon}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  wrap: { flexDirection: "row", alignItems: "center", borderWidth: 1, borderRadius: radius.md },
  button: { width: 38, height: 40, alignItems: "center", justifyContent: "center" },
  value: { ...typography.body, fontWeight: "700", minWidth: 28, textAlign: "center" },
});
