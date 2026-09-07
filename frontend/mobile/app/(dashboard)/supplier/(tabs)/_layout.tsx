import { Tabs } from "expo-router";
import { useQuery } from "@tanstack/react-query";

import { DashboardTabBar } from "@/components/navigation/DashboardTabBar";
import { supplierProfileKey } from "@/features/dashboard/supplier/my-account/hooks/useAccountProfile";
import { getMyProfile } from "@/features/dashboard/supplier/my-account/services/accountService";

/**
 * Supplier dashboard's primary tab group.
 *
 * SAME ARCHITECTURE AS BUSINESS'S _layout.tsx, applied now so both
 * roles share one foundation rather than Business moving to
 * per-screen contextual headers while Supplier is left on the old
 * shared-bar pattern.
 *
 * NO sceneContainerStyle here -- see business/(tabs)/_layout.tsx's
 * docstring for why (not a valid option with a custom tabBar, and not
 * needed for the white-flash fix anyway).
 */
export default function SupplierLayout() {
  /**
   * WARM THE SUPPLIER'S OWN PROFILE as soon as the dashboard mounts.
   *
   * THIS IS HALF OF A HEADER-FLASH FIX, reported directly: the Profile
   * screen showed "Profile" for a beat before swapping to the business
   * name and avatar, because the real title could not exist until a
   * request resolved. (The other half is in ProfileScreen.tsx, which
   * now sets the header from the first render rather than after
   * loading -- see its own comment.)
   *
   * NOT SPECULATIVE PREFETCHING. FOUR screens read this exact cache
   * entry -- My Account, Profile, Supplier visibility and Community
   * activity -- and one of them is reachable from the Community tab's
   * own ⋮, so "the supplier is on a tab" is already good evidence
   * they may open one. It is a single small row for the logged-in
   * user, it is the same queryKey/queryFn those screens use (so this
   * REPLACES their first fetch rather than adding one), and React
   * Query dedupes anything in flight.
   *
   * useQuery rather than prefetchQuery in an effect: the subscription
   * is what keeps the entry from being garbage-collected while the
   * supplier moves between tabs without opening any of the four.
   */
  useQuery({
    queryKey: supplierProfileKey,
    queryFn: getMyProfile,
  });

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
