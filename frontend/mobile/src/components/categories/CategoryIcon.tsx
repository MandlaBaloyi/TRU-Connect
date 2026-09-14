import React from "react";
import {
  Baby,
  Beef,
  Brush,
  Candy,
  Carrot,
  Croissant,
  CupSoda,
  Hammer,
  Milk,
  Package,
  PencilRuler,
  Shapes,
  Shirt,
  ShoppingBasket,
  ShowerHead,
  Smartphone,
  SprayCan,
} from "lucide-react-native";

import type { ProductCategory } from "@/constants/productCategories";

/**
 * One icon per product category.
 *
 * ICONS, NOT PHOTOGRAPHS. Stock photography for seventeen categories
 * costs money we do not have, carries licence obligations nobody wants
 * to track, and dates badly — a 2026 photo of a shelf looks like 2026
 * forever. lucide-react-native is already a dependency, so this is free
 * in every sense, and a line drawing never competes with the product
 * photograph it is standing in for.
 *
 * TWO CHOICES WORTH KNOWING ABOUT, because both look arbitrary and are
 * not:
 *
 *   BEAUTY_HAIR IS A BRUSH, NOT SCISSORS. Scissors say salon, which is
 *   a SERVICE — but nobody buying wigs, relaxers or nail products is
 *   cutting anything. A brush is an actual item in the category and
 *   covers hair and cosmetics both.
 *
 *   AND IT IS NOT Sparkles, which would have been the obvious "beauty"
 *   glyph. Sparkles already means premium in this app — Discovery,
 *   Personalisation and Subscription all use it — so a product
 *   category wearing it would read as a paid feature.
 *
 * EVERY CATEGORY IS PRESENT AND TypeScript ENFORCES IT. The Record type
 * means adding a value to ProductCategory without adding an icon is a
 * compile error rather than a blank square somebody notices in
 * production.
 */
export const CATEGORY_ICONS: Record<
  ProductCategory,
  React.ComponentType<{ size?: number; color?: string; strokeWidth?: number }>
> = {
  FOOD_GROCERY: ShoppingBasket,
  BEVERAGES: CupSoda,
  SNACKS_CONFECTIONERY: Candy,
  BAKERY: Croissant,
  DAIRY_CHILLED: Milk,
  FRESH_PRODUCE: Carrot,
  MEAT_FROZEN: Beef,
  HOUSEHOLD_CLEANING: SprayCan,
  PERSONAL_CARE: ShowerHead,
  BEAUTY_HAIR: Brush,
  BABY_FAMILY: Baby,
  STATIONERY_SCHOOL: PencilRuler,
  HARDWARE_GENERAL: Hammer,
  ELECTRONICS_ACCESSORIES: Smartphone,
  PACKAGING_DISPOSABLE: Package,
  CLOTHING_APPAREL: Shirt,
  OTHER: Shapes,
};

export function CategoryIcon({
  category,
  size = 20,
  color,
  strokeWidth = 1.8,
}: {
  category: ProductCategory | string;
  size?: number;
  color?: string;
  strokeWidth?: number;
}) {
  // A category the app does not know yet (backend ahead of a release)
  // falls back to OTHER rather than rendering nothing.
  const Icon = CATEGORY_ICONS[category as ProductCategory] ?? CATEGORY_ICONS.OTHER;
  return <Icon size={size} color={color} strokeWidth={strokeWidth} />;
}
