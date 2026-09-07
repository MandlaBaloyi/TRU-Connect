import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/shared/settings/components/ComingSoonScreen";

/** COMING_SOON — a real Settings entry with an honest explanation, never
 *  a switch. See shared/settings/types.ts's SettingStatus: TruConnect
 *  must not present a control as functional when changing it wouldn't
 *  affect anything. Notification delivery has no backend behind it
 *  on either role yet, so this stays an explanation until it does. */
export default function NotificationsCommunityScreen() {
  return (
    <ComingSoonScreen
      description="Choose how you hear about your network — a business asking to connect, a business you invited joining, and connections ending."
      examples={["Connection requests", "Invites accepted", "Connections ended"]}
    />
  );
}
