import React from "react";
import { InfoScreen } from "@/features/dashboard/business/settings/components/InfoScreen";
import { TERMS_META_LINE, TERMS_PARAGRAPHS, TERMS_DOWNLOAD_URL } from "@/content/legal/termsContent";

/** Settings-tab wrapper around the shared content — see
 *  content/legal/termsContent.tsx for the actual text and why it's
 *  centralised rather than duplicated here. */
export default function TermsScreen() {
  return (
    <InfoScreen
      metaLine={TERMS_META_LINE}
      paragraphs={TERMS_PARAGRAPHS}
      collapsible
      downloadLink={{ label: "Download as Word document", url: TERMS_DOWNLOAD_URL }}
    />
  );
}
