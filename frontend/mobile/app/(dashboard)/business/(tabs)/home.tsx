import React from "react";
import { StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";
import { useUnreadCount } from "@/features/dashboard/shared/notifications/hooks/useUnreadCount";

/**
 * Home — intentionally empty for now. Do NOT force features in here
 * just because there is available space; Home becomes the daily
 * business overview once enough business activity exists to make it
 * useful, not before.
 */
export default function BusinessDashboardHome() {
  const router = useRouter();
  const { count } = useUnreadCount();

  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      <AppHeader
        variant="brand"
        notificationCount={count}
        onNotificationsPress={() => router.push("/business/notifications" as any)}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({});
