import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/shared/settings/components/ComingSoonScreen";

/**
 * Card/gateway payments — the third row in the Cash / EFT / Card
 * model, not built yet. Reuses the same shared ComingSoonScreen
 * business's own CardPaymentsScreen.tsx already uses — this is a pure
 * presentational shell (description + examples props, no role-
 * specific logic at all), so importing it across the role boundary
 * doesn't create the kind of coupling the rest of this feature
 * deliberately avoids (see ProfileAvatar.tsx's own note on why THAT
 * gets duplicated instead — this component has nothing to duplicate).
 */
export default function CardPaymentsScreen() {
  return (
    <ComingSoonScreen
      description="Get paid directly through a card or payment gateway, with TruConnect integrating with the provider rather than just recording the payment."
      examples={["Card payments", "Payment gateway integrations"]}
    />
  );
}
