import { Tabs } from "expo-router";
import { DashboardTabBar } from "@/components/navigation/DashboardTabBar";

/**
 * Supplier dashboard's primary tab group.
 *
 * SAME ARCHITECTURE AS BUSINESS'S _layout.tsx, applied now so both
 * roles share one foundation rather than Business moving to
 * per-screen contextual headers while Supplier is left on the old
 * shared-bar pattern. Supplier's actual tab CONTENT is intentionally
 * NOT built out yet (deferred, separate work) -- this is the
 * architecture-only pass.
 *
 * NO sceneContainerStyle here -- see business/(tabs)/_layout.tsx's
 * docstring for why (not a valid option with a custom tabBar, and not
 * needed for the white-flash fix anyway).
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
