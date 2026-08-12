import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/business/settings/components/ComingSoonScreen";

/**
 * Card/gateway payments (a payment provider settling to the supplier
 * directly) — the third row in the Cash / EFT / Card model, not built
 * yet. Reuses Settings' existing ComingSoonScreen rather than a new
 * one-off "not built" screen — same component already used for this
 * exact purpose elsewhere in the app.
 */
export default function CardPaymentsScreen() {
  return (
    <ComingSoonScreen
      description="Pay suppliers directly through a card or payment gateway, with TruConnect integrating with the provider rather than just recording the payment."
      examples={["Card payments", "Payment gateway integrations"]}
    />
  );
}
