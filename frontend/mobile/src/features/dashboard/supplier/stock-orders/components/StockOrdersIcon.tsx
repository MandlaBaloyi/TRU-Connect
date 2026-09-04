import React from "react";
import { ClipboardCheck } from "lucide-react-native";
import { palette } from "@/theme/colors";

interface Props {
  size?: number;
}

/**
 * Stock Orders icon. ClipboardCheck reads as "review and decide" --
 * distinct from Products' own Package (what I sell) and Inventory's
 * own Boxes (how much I have). Same construction as every other
 * Account tile icon (emerald green, strokeWidth 2.2, size default 40)
 * so all three tiles read as one consistent set, not a differently
 * themed fourth thing.
 */
export function StockOrdersIcon({ size = 40 }: Props) {
  return <ClipboardCheck size={size} color={palette.emeraldGreen} strokeWidth={2.2} />;
}
