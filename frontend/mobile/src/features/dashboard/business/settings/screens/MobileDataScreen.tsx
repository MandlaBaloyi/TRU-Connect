import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/business/settings/components/ComingSoonScreen";

export default function MobileDataScreen() {
  return (
    <ComingSoonScreen
      description="You'll be able to control how much mobile data TruConnect uses — important when data is expensive."
      examples={["Use mobile data", "Sync over mobile data", "Download media over mobile data"]}
    />
  );
}
