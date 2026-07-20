import React, { useState } from "react";
import { Control, FieldValues, Path } from "react-hook-form";
import { TextInputProps } from "react-native-paper";
import { Eye, EyeOff } from "lucide-react-native";
import { TextInput as RNPTextInput } from "react-native-paper";
import { useTheme } from "react-native-paper";
import { FormTextField } from "./FormTextField";

interface PasswordFieldProps<T extends FieldValues> extends Omit<TextInputProps, "value" | "onChangeText" | "secureTextEntry"> {
  control: Control<T>;
  name: Path<T>;
  label: string;
}

/**
 * Password input with a show/hide toggle (lucide-react-native icons).
 * Ref: master prompt "REUSABLE COMPONENTS" (PasswordField).
 */
export function PasswordField<T extends FieldValues>({ control, name, label, ...rest }: PasswordFieldProps<T>) {
  const theme = useTheme();
  const [visible, setVisible] = useState(false);

  return (
    <FormTextField
      control={control}
      name={name}
      label={label}
      secureTextEntry={!visible}
      right={
        <RNPTextInput.Icon
          icon={() =>
            visible ? (
              <EyeOff size={18} color={theme.colors.onSurfaceVariant} />
            ) : (
              <Eye size={18} color={theme.colors.onSurfaceVariant} />
            )
          }
          onPress={() => setVisible((v) => !v)}
          forceTextInputFocus={false}
        />
      }
      {...rest}
    />
  );
}