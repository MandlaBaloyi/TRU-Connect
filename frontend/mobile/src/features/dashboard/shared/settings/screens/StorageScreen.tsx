import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/shared/settings/components/ComingSoonScreen";

export default function StorageScreen() {
  return (
    <ComingSoonScreen
      description="You'll be able to see how much space TruConnect uses and clear cached data. Clearing cache will never delete your offline business records — those are different things."
      examples={["App storage", "Cached data", "Clear cache"]}
    />
  );
}
