import { useColorScheme as useRNColorScheme } from "react-native";

/**
 * Re-exported so the rest of the app imports colour scheme from a single,
 * app-owned location (easier to swap for a manual theme toggle later).
 *
 * "unspecified" -- a real ColorSchemeName value since RN 0.85 (the device
 * genuinely hasn't declared a preference, distinct from null/undefined) --
 * falls back to the same default as null/undefined, matching this app's
 * pre-existing behaviour rather than introducing a third real UI state
 * nothing in this app was designed around.
 */
export function useColorScheme(): "light" | "dark" {
  const scheme = useRNColorScheme();
  return scheme === "dark" ? "dark" : "light";
}
