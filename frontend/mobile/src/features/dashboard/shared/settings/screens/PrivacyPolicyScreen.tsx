import React from "react";
import { InfoScreen } from "@/features/dashboard/shared/settings/components/InfoScreen";
import { PRIVACY_POLICY_META_LINE, PRIVACY_POLICY_PARAGRAPHS, PRIVACY_POLICY_DOWNLOAD_URL } from "@/content/legal/privacyPolicyContent";

/** Settings-tab wrapper around the shared content — see
 *  content/legal/privacyPolicyContent.tsx for the actual text and why
 *  it's centralised rather than duplicated here. */
export default function PrivacyPolicyScreen() {
  return (
    <InfoScreen
      metaLine={PRIVACY_POLICY_META_LINE}
      paragraphs={PRIVACY_POLICY_PARAGRAPHS}
      collapsible
      downloadLink={{ label: "Download as Word document", url: PRIVACY_POLICY_DOWNLOAD_URL }}
    />
  );
}
