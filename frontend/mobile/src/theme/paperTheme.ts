import { MD3LightTheme, MD3DarkTheme } from "react-native-paper";
import { lightColors, darkColors } from "./colors";
import { radius } from "./spacing";

/**
 * React Native Paper theme configuration, extended with TRU Connect's
 * design tokens. Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt
 */
export const truConnectLightTheme = {
  ...MD3LightTheme,
  roundness: radius.md,
  colors: {
    ...MD3LightTheme.colors,
    primary: lightColors.primary,
    secondary: lightColors.secondary,
    background: lightColors.background,
    surface: lightColors.surface,
    error: lightColors.danger,
    outline: lightColors.border,
    onPrimary: lightColors.onPrimary,
  },
};

export const truConnectDarkTheme = {
  ...MD3DarkTheme,
  roundness: radius.md,
  colors: {
    ...MD3DarkTheme.colors,
    primary: darkColors.primary,
    secondary: darkColors.secondary,
    background: darkColors.background,
    surface: darkColors.surface,
    error: darkColors.danger,
    outline: darkColors.border,
    onPrimary: darkColors.onPrimary,
  },
};
