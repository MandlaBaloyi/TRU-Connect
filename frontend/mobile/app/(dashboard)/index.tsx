import React, { useEffect } from "react";
import { View, ActivityIndicator, StyleSheet } from "react-native";
import { useTheme } from "react-native-paper";
import { useRouter } from "expo-router";
import { getEffectiveRole, isAuthenticated } from "@/navigation/routeGuards";

/**
 * Role-aware dashboard entry point.
 *
 * Reads the authenticated user's role and forwards to the correct
 * dashboard, so sign-in / registration can always redirect to the single
 * stable target "/(dashboard)" without knowing the role.
 *
 * IMPORTANT: this file previously contained a duplicate of the SPLASH
 * screen, which redirected back to /(onboarding)/welcome. Since sign-in
 * redirects here, that produced an infinite loop and the dashboard was
 * unreachable. Do not paste splash-screen content into this file.
 */
export default function DashboardIndex() {
  const router = useRouter();
  const theme = useTheme();

  useEffect(() => {
    (async () => {
      if (!(await isAuthenticated())) {
        router.replace("/(auth)/sign-in");
        return;
      }

      const role = await getEffectiveRole();
      if (role === "supplier") {
        router.replace("/(dashboard)/supplier/home");
      } else {
        router.replace("/(dashboard)/business/home");
      }
    })();
  }, [router]);

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <ActivityIndicator size="large" color={theme.colors.primary} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center" },
});