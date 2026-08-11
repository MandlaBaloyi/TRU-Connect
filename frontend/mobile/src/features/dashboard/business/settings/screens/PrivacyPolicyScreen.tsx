import React from "react";
import { InfoScreen } from "@/features/dashboard/business/settings/components/InfoScreen";
import { PRIVACY_POLICY_META_LINE, PRIVACY_POLICY_PARAGRAPHS } from "@/content/legal/privacyPolicyContent";

/** Settings-tab wrapper around the shared content — see
 *  content/legal/privacyPolicyContent.tsx for the actual text and why
 *  it's centralised rather than duplicated here. */
export default function PrivacyPolicyScreen() {
  return <InfoScreen metaLine={PRIVACY_POLICY_META_LINE} paragraphs={PRIVACY_POLICY_PARAGRAPHS} />;
}
