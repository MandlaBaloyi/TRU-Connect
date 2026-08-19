import React from "react";
import { Package } from "lucide-react-native";
import { palette } from "@/theme/colors";

interface Props {
  size?: number;
}

/**
 * Products icon. Package reads as "what's in the box" — a supplier's
 * catalogue. Same construction as LoanBookIcon/OrderBookIcon (emerald
 * green, strokeWidth 2.2, size default 40) so all three Account tiles
 * read as one consistent set.
 */
export function ProductsIcon({ size = 40 }: Props) {
  return <Package size={size} color={palette.emeraldGreen} strokeWidth={2.2} />;
}
