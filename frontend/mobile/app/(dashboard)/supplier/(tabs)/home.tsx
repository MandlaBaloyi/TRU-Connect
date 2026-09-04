import React from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { UserPlus } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";
import { Card, CardSection, StatusPill } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";
import { useCustomerRequests } from "@/features/dashboard/supplier/customer-requests/hooks/useCustomerRequests";
import { useUnreadCount } from "@/features/dashboard/shared/notifications/hooks/useUnreadCount";

/**
 * Home — architecture-only pass everywhere except Customer Requests
 * (file.txt Phase 3 / FILE2.txt's own "32 businesses want to connect
 * with you" framing) — the first real content on this side of the
 * app, matching the original handoff's "architecture-only, content
 * deferred" now genuinely starting to be filled in, feature by
 * feature, same as the business side was.
 *
 * The card only renders when there's something real to show —
 * zero pending requests means no card, not an empty "0" card
 * cluttering an otherwise-deferred screen.
 */
export default function SupplierDashboardHome() {
  const router = useRouter();
  const theme = useTheme();
  const { requests } = useCustomerRequests();
  const { count } = useUnreadCount();

  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      <AppHeader
        variant="brand"
        notificationCount={count}
        onNotificationsPress={() => router.push("/supplier/notifications" as any)}
      />
      {requests.length > 0 && (
        <View style={styles.section}>
          <CardSection>
            <Card
              icon={(c) => <UserPlus size={20} color={c} />}
              label="Customer requests"
              description={`${requests.length} business${requests.length === 1 ? "" : "es"} want${
                requests.length === 1 ? "s" : ""
              } to connect with you`}
              status={<StatusPill label={String(requests.length)} tone="warning" />}
              onPress={() => router.push("/supplier/customer-requests" as any)}
            />
          </CardSection>
        </View>
      )}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({ section: { paddingHorizontal: spacing.md, paddingTop: spacing.md } });
