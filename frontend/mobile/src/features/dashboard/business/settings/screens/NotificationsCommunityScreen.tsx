import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/shared/settings/components/ComingSoonScreen";

export default function NotificationsCommunityScreen() {
  return (
    <ComingSoonScreen
      description="You'll be able to choose what business network activity you hear about. TruConnect is built to keep this useful, not noisy — you're running a shop, not scrolling a feed."
      examples={["Someone you follow posted", "Business network activity", "New discussion"]}
    />
  );
}
