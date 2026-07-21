import { Tabs } from "expo-router";
import { DashboardTabBar } from "@/components/navigation/DashboardTabBar";

/**
 * Top-level dashboard layout. Registers the role-aware index redirect
 * plus the two fully separate dashboard route groups. Business and
 * Supplier screens never share a route -- only shared UI components
 * (like DashboardTabBar) are reused between them.
 * Ref: master prompt "There are TWO completely different dashboards".
 */
export default function SupplierLayout() {
  return (
    <Tabs
      tabBar={(props) => <DashboardTabBar {...props} />}
      screenOptions={{ headerShown: false }}
    >
      <Tabs.Screen name="home" options={{ title: "Home" }} />
      <Tabs.Screen name="account" options={{ title: "Account" }} />
      <Tabs.Screen name="community" options={{ title: "Community" }} />
      <Tabs.Screen name="discovery" options={{ title: "Discovery" }} />
      <Tabs.Screen name="more" options={{ title: "More" }} />
    </Tabs>
  );
}