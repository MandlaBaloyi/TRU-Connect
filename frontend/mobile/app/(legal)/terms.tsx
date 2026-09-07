import React from "react";
import { InfoScreen } from "@/features/dashboard/shared/settings/components/InfoScreen";
import { TERMS_META_LINE, TERMS_PARAGRAPHS, TERMS_DOWNLOAD_URL } from "@/content/legal/termsContent";

/** Public, pre-auth Terms of Service — see content/legal/termsContent.tsx
 *  for the shared text. */
export default function PublicTermsScreen() {
  return (
    <InfoScreen
      metaLine={TERMS_META_LINE}
      paragraphs={TERMS_PARAGRAPHS}
      collapsible
      downloadLink={{ label: "Download as Word document", url: TERMS_DOWNLOAD_URL }}
    />
  );
}
