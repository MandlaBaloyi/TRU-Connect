import React, { useState } from "react";
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Bell } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";
import { ErrorState } from "@/components/feedback/ErrorState";
import { EmptyState } from "@/components/feedback/EmptyState";

import { useNotifications } from "../hooks/useNotifications";
import { useMarkAsRead } from "../hooks/useMarkAsRead";
import { NotificationRow } from "../components/NotificationRow";
import { NotificationsMenu } from "../components/NotificationsMenu";
import { NotificationDetailSheet } from "../components/NotificationDetailSheet";
import type { Notification, NotificationCategory } from "../types";

const TABS = [
  { key: "STOCK_ORDER", label: "Stock Orders" },
  { key: "INBOX", label: "Inbox" },
];

/**
 * The real notification screen -- genuinely role-agnostic (reached
 * identically from both business/notifications.tsx and
 * supplier/notifications.tsx, matching shared/connections' own
 * proven "thin route, shared implementation" precedent).
 *
 * USES AppHeader's OWN "title-with-tabs" VARIANT -- a real fix,
 * confirmed directly: this used to render "Notifications" via the
 * NATIVE Stack header (a completely separate rendering system from
 * this screen's own JSX) with the Stock Orders/Inbox tabs as a
 * second, separately-rendered row underneath -- two different
 * mechanisms, stacked, not one bar. "title-with-tabs" is the
 * dedicated variant already BUILT for exactly this shape (title
 * directly above tabs, nothing between them) -- Community itself
 * doesn't use it only because it needs extra content (an "Invite a
 * business" row) between its own title and tabs; this screen has no
 * such content, so the purpose-built variant is the correct choice
 * here, not Community's own manually-composed workaround.
 *
 * THE 3-DOT MENU reuses the same proven trick as
 * CommunityOverflowMenu.tsx: the whole self-contained NotificationsMenu
 * (its own Menu + anchor Pressable) is passed directly as AppHeader's
 * own rightIcon, with onRightIconPress left undefined -- AppHeader's
 * own outer Pressable wrapper goes inert with no handler, and
 * NotificationsMenu's own inner Pressable does the real work.
 *
 * TAPPING A ROW marks it read and shows its own full message --
 * deliberately NOT a deep-link into any order-management screen. A
 * REAL BUG FOUND AND FIXED after direct report: an earlier version
 * unconditionally routed every stock_order tap to the business-only
 * cart route, regardless of who was actually tapping -- a supplier
 * opening their own "new order" notification got sent into a request
 * the backend correctly rejected with 403. Confirmed directly: the
 * full order-management screen (items, price, payment method,
 * Approve/Decline) is real, separate, core supplier functionality
 * this notification will eventually link INTO once it exists -- not
 * something this feature owns or should half-build itself. Showing
 * the notification's own full, unclipped message IS this feature's
 * whole job finishing, not a placeholder standing in for more.
 */
export default function NotificationsScreen() {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState<NotificationCategory>("STOCK_ORDER");
  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null);
  const { notifications, isLoading, isError, refetch, isRefetching } = useNotifications(activeTab);
  const { markAsRead, markAllAsRead } = useMarkAsRead();

  const handlePress = (notification: Notification) => {
    if (!notification.isRead) {
      markAsRead(notification.id).catch(() => {
        // Silently ignored -- a failed mark-as-read should never
        // block the person from seeing their own message; they can
        // simply see it again next time.
      });
    }
    setSelectedNotification(notification);
  };

  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      <AppHeader
        variant="title-with-tabs"
        title="Notifications"
        showBackButton
        rightIcon={<NotificationsMenu onMarkAllAsRead={() => markAllAsRead()} />}
        tabs={TABS}
        activeTab={activeTab}
        onTabChange={(key) => setActiveTab(key as NotificationCategory)}
        tabsAlign="columns"
      />

      {isLoading ? (
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      ) : isError ? (
        <ErrorState message="Couldn't load your notifications. Check your connection and try again." onRetry={refetch} />
      ) : notifications.length === 0 ? (
        <EmptyState
          icon={<Bell size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
          message={activeTab === "STOCK_ORDER" ? "No order notifications yet." : "No messages yet."}
        />
      ) : (
        <FlatList
          data={notifications}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <NotificationRow notification={item} onPress={() => handlePress(item)} />}
          refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={theme.colors.primary} />}
        />
      )}

      <NotificationDetailSheet notification={selectedNotification} onClose={() => setSelectedNotification(null)} />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
});
