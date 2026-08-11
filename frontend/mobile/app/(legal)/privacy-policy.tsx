import React from "react";
import { InfoScreen } from "@/features/dashboard/business/settings/components/InfoScreen";
import { PRIVACY_POLICY_META_LINE, PRIVACY_POLICY_PARAGRAPHS } from "@/content/legal/privacyPolicyContent";

/** Public, pre-auth Privacy Policy — see
 *  content/legal/privacyPolicyContent.tsx for the shared text. */
export default function PublicPrivacyPolicyScreen() {
  return <InfoScreen metaLine={PRIVACY_POLICY_META_LINE} paragraphs={PRIVACY_POLICY_PARAGRAPHS} />;
}
