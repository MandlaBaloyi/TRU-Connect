import React from "react";
import { Boxes } from "lucide-react-native";
import { palette } from "@/theme/colors";

interface Props {
  size?: number;
}

/**
 * Product Catalogue icon.
 *
 * Uses Lucide's Boxes icon to represent:
 * - Product Catalogue
 * - Inventory
 * - Stock Management
 * - Supplier Products
 *
 * Consistent with the TruConnect design system.
 */
export function ProductCatalogueIcon({ size = 40 }: Props) {
  return (
    <Boxes
      size={size}
      color={palette.emeraldGreen}
      strokeWidth={2.2}
    />
  );
}