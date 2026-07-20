import { useColorScheme as useRNColorScheme } from "react-native";

/**
 * Re-exported so the rest of the app imports colour scheme from a single,
 * app-owned location (easier to swap for a manual theme toggle later).
 */
export function useColorScheme(): "light" | "dark" {
  return useRNColorScheme() ?? "light";
}
