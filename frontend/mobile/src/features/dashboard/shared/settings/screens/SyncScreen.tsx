import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/shared/settings/components/ComingSoonScreen";

export default function SyncScreen() {
  return (
    <ComingSoonScreen
      description="You'll be able to see exactly when your business information last synced, how many changes are still pending, and sync on demand."
      examples={["Last synced time", "Pending changes", "Sync now", "Automatic sync"]}
    />
  );
}
