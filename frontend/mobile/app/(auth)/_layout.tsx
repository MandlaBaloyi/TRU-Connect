import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";

/**
 * Nested Stack for the (auth) group -- needs its OWN contentStyle fix,
 * independently of the root layout's ThemedStack: a nested navigator
 * does not inherit the parent Stack's screenOptions automatically, so
 * without this, Sign In / Create Account / etc. would still show the
 * same white-flash-on-swipe bug even after the root layout is fixed.
 */
export default function AuthLayout() {
  const theme = useTheme();
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    />
  );
}