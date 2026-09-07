import React from "react";
import { InfoScreen } from "@/features/dashboard/shared/settings/components/InfoScreen";
import { PRIVACY_POLICY_META_LINE, PRIVACY_POLICY_PARAGRAPHS, PRIVACY_POLICY_DOWNLOAD_URL } from "@/content/legal/privacyPolicyContent";

/** Public, pre-auth Privacy Policy — see
 *  content/legal/privacyPolicyContent.tsx for the shared text. */
export default function PublicPrivacyPolicyScreen() {
  return (
    <InfoScreen
      metaLine={PRIVACY_POLICY_META_LINE}
      paragraphs={PRIVACY_POLICY_PARAGRAPHS}
      collapsible
      downloadLink={{ label: "Download as Word document", url: PRIVACY_POLICY_DOWNLOAD_URL }}
    />
  );
}
