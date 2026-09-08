import type { Metadata } from "next";

import { Pricing } from "@/surfaces/marketing/Pricing";

export const metadata: Metadata = {
  title: "Pricing",
  description:
    "Start free and take orders from businesses on TruConnect. Talk to us when your catalogue outgrows a spreadsheet.",
};

export default function PricingPage() {
  return <Pricing />;
}
