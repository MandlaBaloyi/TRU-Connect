import type { Metadata } from "next";

import { About } from "@/surfaces/marketing/About";

export const metadata: Metadata = {
  title: "About",
  description:
    "TruConnect connects South Africa's independent shops with the suppliers who stock them. Part of the TruePoint platform.",
};

/** `/about`. Body in `src/surfaces/marketing/About.tsx`. */
export default function AboutPage() {
  return <About />;
}
