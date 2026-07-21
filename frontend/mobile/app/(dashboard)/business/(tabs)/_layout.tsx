import { Tabs } from "expo-router";
import { DashboardTabBar } from "@/components/navigation/DashboardTabBar";

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