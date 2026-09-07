import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/shared/settings/components/ComingSoonScreen";

export default function NotificationsDiscoveryScreen() {
  return (
    <ComingSoonScreen
      description="You'll be able to choose which opportunities and useful information TruConnect tells you about."
      examples={["Business opportunities", "Supplier offers", "Educational content", "Relevant programmes", "Financing opportunities"]}
    />
  );
}
