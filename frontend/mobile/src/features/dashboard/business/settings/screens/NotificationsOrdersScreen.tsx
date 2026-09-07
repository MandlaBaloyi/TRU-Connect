import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/shared/settings/components/ComingSoonScreen";

export default function NotificationsOrdersScreen() {
  return (
    <ComingSoonScreen
      description="TruConnect will notify you about important stock orders and delivery updates when this feature is available."
      examples={["New stock order received", "Order accepted", "Order dispatched", "Order delivered", "Order cancelled"]}
    />
  );
}
