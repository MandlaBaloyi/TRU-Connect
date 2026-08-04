import React from "react";
import { NotebookPen } from "lucide-react-native";
import { palette } from "@/theme/colors";

interface Props {
  size?: number;
}

/**
 * Loan Book icon.
 *
 * Uses Lucide's NotebookPen to represent:
 * - Loan Book
 * - Credit sales recorded by hand
 * - The paper "Pay Later" book this feature replaces
 *
 * DELIBERATELY NOT a banknote, coin, wallet, or currency symbol.
 * TRUConnect does not lend, hold funds, or collect (Doc 04 §3.5) — a
 * money icon would quietly imply a financial product this feature is
 * explicitly not. A notebook says "this replaces your paper book",
 * which is exactly what it does.
 *
 * Matches ProductCatalogueIcon's construction: same emerald green, same
 * strokeWidth, same size default, so tiles in the Account grid read as
 * one consistent set.
 */
export function LoanBookIcon({ size = 40 }: Props) {
  return (
    <NotebookPen
      size={size}
      color={palette.emeraldGreen}
      strokeWidth={2.2}
    />
  );
}
