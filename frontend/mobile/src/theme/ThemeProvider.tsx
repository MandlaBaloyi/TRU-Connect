import React from "react";
import { PaperProvider } from "react-native-paper";
import { useColorScheme } from "@/hooks/useColorScheme";
import { truConnectLightTheme, truConnectDarkTheme } from "./paperTheme";

/**
 * Wraps the application with a React Native Paper theme that responds to
 * the device colour scheme.
 * Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 1.5 (Accessibility)
 */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const scheme = useColorScheme();
  const theme = scheme === "dark" ? truConnectDarkTheme : truConnectLightTheme;
  return <PaperProvider theme={theme}>{children}</PaperProvider>;
}
