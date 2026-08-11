import React, { useEffect } from "react";
import { PaperProvider } from "react-native-paper";
import * as SystemUI from "expo-system-ui";
import { useColorScheme } from "@/hooks/useColorScheme";
import { useSettings } from "@/features/dashboard/business/settings/hooks/SettingsProvider";
import { truConnectLightTheme, truConnectDarkTheme } from "./paperTheme";

/**
 * Wraps the application with a React Native Paper theme.
 *
 * THE USER'S SAVED THEME PREFERENCE WINS over the device colour
 * scheme — "System default" explicitly falls back to the device, but
 * an explicit Light/Dark choice in Settings must be respected on every
 * screen in the app. That's the whole point of the Theme setting being
 * REAL rather than cosmetic; see settings/types.ts's SettingStatus.
 *
 * Requires SettingsProvider to be mounted ABOVE this component (see
 * app/_layout.tsx) — useSettings() falls back to DEFAULT_SETTINGS if
 * it isn't, which would silently pin the app to "SYSTEM" and make the
 * Theme setting appear broken.
 *
 * ALSO SETS THE NATIVE ROOT VIEW BACKGROUND (expo-system-ui), NOT JUST
 * REACT NAVIGATION'S contentStyle. This is a real, separate remaining
 * gap: contentStyle is React Navigation's OWN styling layer, applied
 * per-screen. It's confirmed correct on every navigator in this app
 * now (see app/_layout.tsx's own docstring on that sweep) — but
 * router.replace() across a top-level group boundary (exactly what
 * login/logout do: (auth) -> (dashboard), and (dashboard) -> another
 * (dashboard) route for the role-based redirect in
 * app/(dashboard)/index.tsx) can involve a genuine remount of the
 * destination navigator tree, and for a brief moment during that
 * remount there is no React-rendered content there at all yet -- what
 * shows through in that gap is whatever the NATIVE Android window's
 * OWN background is, a layer BELOW anything React Navigation controls.
 * That native background was never set anywhere in this app and
 * defaults to white. setBackgroundColorAsync sets that native layer
 * directly, so even a brief "nothing painted yet" moment shows the
 * correct theme colour instead of white.
 */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const deviceScheme = useColorScheme();
  const { settings } = useSettings();

  const effectiveScheme =
    settings.theme === "SYSTEM" ? deviceScheme : settings.theme === "DARK" ? "dark" : "light";

  const theme = effectiveScheme === "dark" ? truConnectDarkTheme : truConnectLightTheme;

  useEffect(() => {
    SystemUI.setBackgroundColorAsync(theme.colors.background);
  }, [theme.colors.background]);

  return <PaperProvider theme={theme}>{children}</PaperProvider>;
}
