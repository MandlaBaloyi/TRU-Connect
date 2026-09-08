import type { Metadata } from "next";

import { Contact } from "@/surfaces/marketing/Contact";

export const metadata: Metadata = {
  title: "Contact",
  description:
    "How to reach TruConnect: in the app for account questions, the supplier area for suppliers, email for everything else.",
};

/** `/contact`. Body in `src/surfaces/marketing/Contact.tsx`. */
export default function ContactPage() {
  return <Contact />;
}
