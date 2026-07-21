import React, { useEffect } from "react";
import { View, ActivityIndicator, StyleSheet } from "react-native";
import { useTheme } from "react-native-paper";
import { useRouter } from "expo-router";
import { getSelectedRole } from "@/navigation/routeGuards";

/**
 * Role-aware dashboard entry point. Redirects to the Business or
 * Supplier dashboard based on the role stored at registration/role
 * selection (src/navigation/routeGuards.ts), so "/(dashboard)" is a
 * single, stable redirect target for sign-in/sign-up flows regardless of
 * role -- neither useAuth.ts nor verify-otp needs to know which concrete
 * dashboard route to target.
 * Ref: master prompt "There are TWO completely different dashboards".
 */
export default function DashboardIndex() {
  const router = useRouter();
  const theme = useTheme();

  useEffect(() => {
    (async () => {
      const role = await getSelectedRole();
      if (role === "supplier") {
        router.replace("/(dashboard)/supplier/(tabs)/home");
      } else {
        router.replace("/(dashboard)/business/(tabs)/home");
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