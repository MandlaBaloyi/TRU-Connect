import type { Metadata } from "next";

import { LegalDocument } from "@/surfaces/marketing/LegalDocument";
import { PRIVACY } from "@/surfaces/marketing/legalContent";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description:
    "How TRU Connect handles personal information, with reference to POPIA. Draft, pending legal review.",
};

/** `/privacy`. Text in `src/surfaces/marketing/legalContent.ts`. */
export default function PrivacyPage() {
  return <LegalDocument doc={PRIVACY} />;
}
