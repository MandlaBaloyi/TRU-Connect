import React from "react";
import { ComingSoonScreen } from "@/features/dashboard/shared/settings/components/ComingSoonScreen";

export default function ReportProblemScreen() {
  return (
    <ComingSoonScreen
      description="You'll be able to report a problem directly to the TruConnect team, with the right diagnostic information attached automatically — without exposing your private business data."
      examples={["Order problem", "Loan Book problem", "Account problem", "Supplier problem", "App problem"]}
    />
  );
}
