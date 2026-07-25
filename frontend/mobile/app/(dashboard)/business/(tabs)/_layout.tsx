import { Tabs } from "expo-router";
import { DashboardTabBar } from "@/components/navigation/DashboardTabBar";
import { BrandTopBar, TopBarScrollProvider } from "@/components/navigation/BrandTopBar";

/**
 * Business dashboard's primary tab group. BrandTopBar + TopBarScrollProvider
 * are mounted once here so every primary screen (home/account/community/
 * discovery/more) shares the same scroll-hide brand bar. Feature screens
 * pushed outside this (tabs) group never see this bar or the tab bar.
 */
export default function BusinessLayout() {
  return (
    <TopBarScrollProvider>
      <BrandTopBar />
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
    </TopBarScrollProvider>
  );
}