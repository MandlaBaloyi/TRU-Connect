import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/shared/settings/components/ComingSoonScreen";

export default function BusinessVisibilityScreen() {
  return (
    <ComingSoonScreen
      description="You'll be able to control how visible your business is to others on TruConnect."
      examples={["Private", "Connected businesses only", "Public"]}
    />
  );
}
