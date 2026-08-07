import React from "react";
import { ClipboardList } from "lucide-react-native";
import { palette } from "@/theme/colors";

interface Props {
  size?: number;
}

/**
 * Order Book icon. ClipboardList reads as "a running list of orders to
 * work through" — the queue this feature replaces. Same construction as
 * LoanBookIcon (emerald green, strokeWidth 2.2, size default 40) so both
 * tiles read as one consistent set on the Account grid.
 */
export function OrderBookIcon({ size = 40 }: Props) {
  return <ClipboardList size={size} color={palette.emeraldGreen} strokeWidth={2.2} />;
}
