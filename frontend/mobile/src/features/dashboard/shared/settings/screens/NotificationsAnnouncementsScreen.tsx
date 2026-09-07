import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/shared/settings/components/ComingSoonScreen";

export default function NotificationsAnnouncementsScreen() {
  return (
    <ComingSoonScreen
      description="Important platform communications from TruConnect. Critical service and security notices will always be delivered regardless of this setting."
      examples={["Scheduled maintenance", "New features", "Important service information"]}
    />
  );
}
