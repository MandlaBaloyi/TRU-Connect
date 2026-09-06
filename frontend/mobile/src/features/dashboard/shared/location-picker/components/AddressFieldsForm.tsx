import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { TextInput, useTheme } from "react-native-paper";

import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { DeliveryLocation } from "../types";

interface Props {
  values: Omit<DeliveryLocation, "latitude" | "longitude">;
  onChange: (field: keyof Omit<DeliveryLocation, "latitude" | "longitude">, value: string) => void;
}

/**
 * Uses react-native-paper's own TextInput (mode="outlined"), same
 * component FormTextField.tsx already wraps elsewhere in this app --
 * NOT a plain RN TextInput with a placeholder. The real, reported
 * problem with the placeholder version: once a field like Street has
 * a value in it ("University Road"), the placeholder text disappears
 * entirely, so a business coming back to EDIT it has no label telling
 * them which field is which. Paper's outlined TextInput keeps the
 * label visible, floated to the top edge of the field, for exactly
 * this reason -- matches this app's own spec (labels always visible,
 * docs/02_SYSTEM_UI_UX_SPECIFICATION.txt Section 9) rather than
 * introducing a new pattern.
 */
export function AddressFieldsForm({ values, onChange }: Props) {
  const theme = useTheme();

  return (
    <View style={styles.container}>
      <TextInput
        mode="outlined"
        label="Building or landmark (optional)"
        value={values.building}
        onChangeText={(text) => onChange("building", text)}
        contentStyle={styles.inputContent}
      />
      <TextInput
        mode="outlined"
        label="Street"
        value={values.street}
        onChangeText={(text) => onChange("street", text)}
        contentStyle={styles.inputContent}
      />
      <View style={styles.row}>
        <TextInput
          mode="outlined"
          label="Suburb"
          value={values.suburb}
          onChangeText={(text) => onChange("suburb", text)}
          contentStyle={styles.inputContent}
          style={styles.half}
        />
        <TextInput
          mode="outlined"
          label="City"
          value={values.city}
          onChangeText={(text) => onChange("city", text)}
          contentStyle={styles.inputContent}
          style={styles.half}
        />
      </View>
      <View style={styles.row}>
        <TextInput
          mode="outlined"
          label="Province"
          value={values.province}
          onChangeText={(text) => onChange("province", text)}
          contentStyle={styles.inputContent}
          style={styles.half}
        />
        <TextInput
          mode="outlined"
          label="Postal code"
          value={values.postalCode}
          onChangeText={(text) => onChange("postalCode", text)}
          keyboardType="number-pad"
          contentStyle={styles.inputContent}
          style={styles.half}
        />
      </View>
      <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>
        Filled in from the map -- check it's right and fix anything that's off.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: spacing.sm },
  row: { flexDirection: "row", gap: spacing.sm },
  half: { flex: 1 },
  inputContent: { paddingVertical: 2 },
  hint: { ...typography.bodySmall, marginTop: spacing.xs },
});

