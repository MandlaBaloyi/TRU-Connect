import type { Metadata } from "next";

import { HowItWorks } from "@/surfaces/marketing/HowItWorks";

export const metadata: Metadata = {
  title: "How it works",
  description:
    "How businesses find and order stock, and how suppliers list their products and take orders on TruConnect.",
};

export default function HowItWorksPage() {
  return <HowItWorks />;
}
