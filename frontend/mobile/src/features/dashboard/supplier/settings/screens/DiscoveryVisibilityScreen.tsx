import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/shared/settings/components/ComingSoonScreen";

/** COMING_SOON — a real Settings entry with an honest explanation, never
 *  a switch. See shared/settings/types.ts's SettingStatus: TruConnect
 *  must not present a control as functional when changing it wouldn't
 *  affect anything. The real toggles for this move here from the
 *  supplier's profile once this shell is reviewed. */
export default function DiscoveryVisibilityScreen() {
  return (
    <ComingSoonScreen
      description="Control whether your business appears in Discovery, and how you're presented to businesses who haven't connected with you yet. Discovery itself is still being built."
      examples={["Appear in Discovery", "Featured categories", "Promoted stock"]}
    />
  );
}
