/**
 * TRU Connect design tokens - colour palette.
 * Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 5 (Color Palette)
 *
 * Functional colour roles rather than raw hex usage across the app, so
 * theming (including dark mode) can be layered on without redesign.
 * NEVER hardcode colours in screens/components -- always import from here.
 */
export const palette = {
  truePointBlue: "#0B2447",
  truePointBlueLight: "#19376D",
  truePointBlueDark: "#051230",

  emeraldGreen: "#0FA968",
  emeraldGreenLight: "#3FCB8C",
  emeraldGreenDark: "#0A7A4C",

  neutral900: "#111417",
  neutral700: "#3A3F44",
  neutral500: "#6B7280",
  neutral300: "#D0D4D9",
  neutral100: "#F4F6F8",
  white: "#FFFFFF",

  danger: "#D64545",
  warning: "#E1A400",
  success: "#0FA968",
} as const;

export const lightColors = {
  primary: palette.truePointBlue,
  primaryDark: palette.truePointBlueDark,
  secondary: palette.emeraldGreen,
  success: palette.success,
  warning: palette.warning,
  danger: palette.danger,
  background: palette.white,
  surface: palette.neutral100,
  border: palette.neutral300,
  textPrimary: palette.neutral900,
  textSecondary: palette.neutral500,
  onPrimary: palette.white,
};

export const darkColors = {
  primary: palette.truePointBlueLight,
  primaryDark: palette.truePointBlue,
  secondary: palette.emeraldGreenLight,
  success: palette.emeraldGreenLight,
  warning: palette.warning,
  danger: palette.danger,
  background: palette.neutral900,
  surface: "#1B1F24",
  border: "#2C3238",
  textPrimary: palette.white,
  textSecondary: palette.neutral300,
  onPrimary: palette.white,
};

export type AppColors = typeof lightColors;
