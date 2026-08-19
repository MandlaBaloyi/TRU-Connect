import React from "react";
import { Boxes } from "lucide-react-native";
import { palette } from "@/theme/colors";

interface Props {
  size?: number;
}

/**
 * Inventory icon. Boxes reads as "how much stock do I actually have" --
 * distinct from Products' own Package icon (what I sell vs. how much
 * of it). Same construction as every other Account tile icon (emerald
 * green, strokeWidth 2.2, size default 40).
 */
export function InventoryIcon({ size = 40 }: Props) {
  return <Boxes size={size} color={palette.emeraldGreen} strokeWidth={2.2} />;
}
