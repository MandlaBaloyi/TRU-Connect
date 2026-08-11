import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/business/settings/components/ComingSoonScreen";

export default function PersonalisationScreen() {
  return (
    <ComingSoonScreen
      description="You'll be able to choose whether TruConnect uses your business activity to make Discovery more relevant to you."
      examples={["Educational content for your business", "Opportunities relevant to your industry", "Supplier-related information"]}
    />
  );
}
