import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/shared/settings/components/ComingSoonScreen";

/** COMING_SOON — a real Settings entry with an honest explanation, never
 *  a switch. See shared/settings/types.ts's SettingStatus: TruConnect
 *  must not present a control as functional when changing it wouldn't
 *  affect anything. Auto-decline and approval rules are real backend
 *  questions that nothing implements yet, so this stays an explanation
 *  rather than a switch that silently does nothing. */
export default function SupplierPreferencesScreen() {
  return (
    <ComingSoonScreen
      description="Set defaults for how you handle stock orders — how long before an unanswered order auto-declines, and whether new orders need your approval at all."
      examples={["Auto-decline window", "Approval required", "Default order note"]}
    />
  );
}
