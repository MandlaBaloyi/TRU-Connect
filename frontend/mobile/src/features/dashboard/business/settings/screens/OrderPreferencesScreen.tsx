import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/shared/settings/components/ComingSoonScreen";

export default function OrderPreferencesScreen() {
  return (
    <ComingSoonScreen
      description="You'll be able to set how stock ordering behaves for your business by default."
      examples={["Default stock order status", "Preferred supplier ordering", "Order confirmation before sending", "Delivery update preferences"]}
    />
  );
}
