import React, { useRef } from "react";
import { View, TextInput as RNTextInput, StyleSheet } from "react-native";
import { useTheme } from "react-native-paper";
import { OTP_LENGTH } from "@/constants/config";
import { spacing, radius } from "@/theme/spacing";

interface OtpInputProps {
  value: string;
  onChange: (value: string) => void;
  length?: number;
}

/**
 * Segmented OTP entry boxes. Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt
 * (OTP Verification screen).
 */
export function OtpInput({ value, onChange, length = OTP_LENGTH }: OtpInputProps) {
  const theme = useTheme();
  const inputRef = useRef<RNTextInput>(null);
  const digits = value.split("");

  return (
    <View style={styles.row}>
      {/* Single hidden input drives all boxes for reliable focus/keyboard handling */}
      <RNTextInput
        ref={inputRef}
        value={value}
        onChangeText={(text) => onChange(text.replace(/[^0-9]/g, "").slice(0, length))}
        keyboardType="number-pad"
        maxLength={length}
        style={styles.hiddenInput}
        autoFocus
      />
      {Array.from({ length }).map((_, i) => {
        const filled = !!digits[i];
        return (
          <View
            key={i}
            style={[
              styles.box,
              {
                borderColor: filled ? theme.colors.primary : theme.colors.outline,
                backgroundColor: theme.colors.surface,
              },
            ]}
          >
            <View>
              <RNTextInput
                editable={false}
                value={digits[i] ?? ""}
                style={[styles.boxText, { color: theme.colors.onSurface }]}
              />
            </View>
          </View>
        );
      })}
    </View>
  );
}

const BOX_SIZE = 48;

const styles = StyleSheet.create({
  row: { flexDirection: "row", justifyContent: "space-between", marginVertical: spacing.lg },
  box: {
    width: BOX_SIZE,
    height: BOX_SIZE,
    borderRadius: radius.sm,
    borderWidth: 2,
    alignItems: "center",
    justifyContent: "center",
  },
  boxText: { fontSize: 20, fontWeight: "700", textAlign: "center" },
  hiddenInput: { position: "absolute", opacity: 0, height: 1, width: 1 },
});
