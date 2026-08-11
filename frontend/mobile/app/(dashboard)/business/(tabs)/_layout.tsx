import { Tabs } from "expo-router";
import { DashboardTabBar } from "@/components/navigation/DashboardTabBar";

/**
 * Business dashboard's primary tab group.
 *
 * OWNS BOTTOM NAVIGATION ONLY -- no shared top bar mounted here
 * anymore. Each of the 5 screens (home/account/community/discovery/
 * more) now owns its own contextual header, its own content, and its
 * own scrolling behaviour independently, all through one AppHeader
 * component with a variant prop. Previously a single BrandTopBar
 * was mounted here and shared identically across all 5 tabs -- that
 * was the actual problem: every tab showing the same generic
 * "TruConnect" bar regardless of which section you were in, when the
 * top bar should answer "where am I", not just "what app is this".
 *
 * NO sceneContainerStyle here: it isn't a valid screenOptions key for
 * Tabs when a custom tabBar is supplied (confirmed by TypeScript, not
 * assumed) -- and it isn't needed for the white-flash fix anyway, since
 * every individual tab screen already sets its own theme-aware
 * background via ScreenContainer, and tab switches don't reveal a gap
 * the way Stack push/pop transitions do.
 */
export default function BusinessLayout() {
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
