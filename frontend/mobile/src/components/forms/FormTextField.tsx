import React from "react";
import { Controller, Control, FieldValues, Path } from "react-hook-form";
import { HelperText, TextInput, TextInputProps } from "react-native-paper";
import { View } from "react-native";
import { spacing } from "@/theme/spacing";

interface FormTextFieldProps<T extends FieldValues> extends Omit<TextInputProps, "value" | "onChangeText"> {
  control: Control<T>;
  name: Path<T>;
  label: string;
}

/**
 * React Hook Form <-> React Native Paper TextInput bridge, with inline
 * validation error display. Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt,
 * Section 9 (Forms) - labels always visible, inline errors in Danger role.
 */
export function FormTextField<T extends FieldValues>({
  control,
  name,
  label,
  secureTextEntry,
  ...rest
}: FormTextFieldProps<T>) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field: { onChange, onBlur, value }, fieldState: { error } }) => (
        <View style={{ marginBottom: spacing.sm }}>
          <TextInput
            mode="outlined"
            label={label}
            value={value ?? ""}
            onChangeText={onChange}
            onBlur={onBlur}
            secureTextEntry={secureTextEntry}
            error={!!error}
            contentStyle={{ paddingVertical: 2 }}
            {...rest}
          />
          {error && (
            <HelperText type="error" visible>
              {error.message}
            </HelperText>
          )}
        </View>
      )}
    />
  );
}