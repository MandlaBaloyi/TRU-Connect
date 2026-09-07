import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/shared/settings/components/ComingSoonScreen";

/** COMING_SOON — a real Settings entry with an honest explanation, never
 *  a switch. See shared/settings/types.ts's SettingStatus: TruConnect
 *  must not present a control as functional when changing it wouldn't
 *  affect anything. Notification delivery has no backend behind it
 *  on either role yet, so this stays an explanation until it does. */
export default function NotificationsOrdersScreen() {
  return (
    <ComingSoonScreen
      description="Choose how you hear about incoming stock orders — a new order waiting for your approval, an order a business cancelled, and reminders before an order auto-declines."
      examples={["New order received", "Order cancelled by business", "Auto-decline reminders"]}
    />
  );
}
