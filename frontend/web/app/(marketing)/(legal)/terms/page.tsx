import type { Metadata } from "next";

import { LegalDocument } from "@/surfaces/marketing/LegalDocument";
import { TERMS } from "@/surfaces/marketing/legalContent";

export const metadata: Metadata = {
  title: "Terms of Service",
  description:
    "The terms that govern use of TRU Connect. Draft, pending legal review.",
};

/** `/terms`. Text in `src/surfaces/marketing/legalContent.ts`. */
export default function TermsPage() {
  return <LegalDocument doc={TERMS} />;
}
