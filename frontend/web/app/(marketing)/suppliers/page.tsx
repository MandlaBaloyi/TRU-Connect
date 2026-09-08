import type { Metadata } from "next";

import { Suppliers } from "@/surfaces/marketing/Suppliers";

export const metadata: Metadata = {
  title: "For suppliers",
  description:
    "Reach the shops already buying what you sell. Set your catalogue up on the web, run the day from the app, and keep your own terms.",
};

/**
 * `/suppliers` -- the route from the public site into the portal.
 * Body in `src/surfaces/marketing/Suppliers.tsx`.
 */
export default function SuppliersPage() {
  return <Suppliers />;
}
