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

/**
 * The same icons, reachable by NAME, for the server-supplied
 * FeedCategory.icon.
 *
 * WHY THIS IS A MAP AND NOT `import * as lucide`. A namespace import of
 * lucide-react-native defeats tree-shaking and drags roughly a thousand
 * icon components into the bundle -- a real cost on a phone in a shop
 * with a metered connection, paid by every user forever, to cover a
 * case that happens when a category is added.
 *
 * SO THE CONTRACT IS HONOURED WITH ONE HONEST LIMIT. FeedCategory.icon
 * is documented as "server-chosen so a new category doesn't need an app
 * release to get an icon", and that holds for any icon in this map --
 * the server can move a category to a different one of these freely. A
 * genuinely NEW glyph still needs a release; until then the category
 * appears with the neutral fallback rather than not appearing at all,
 * which is the part that actually matters.
 *
 * WRITTEN OUT RATHER THAN DERIVED FROM displayName. Building this from
 * `Icon.displayName` would depend on an undocumented property of
 * lucide-react-native; if it were ever undefined the whole map would
 * collapse to a single "" key and every server-supplied name would
 * silently miss -- failing softly, in the direction that looks like it
 * works. Seventeen literal lines cannot do that.
 */
const ICONS_BY_NAME: Record<
  string,
  React.ComponentType<{ size?: number; color?: string; strokeWidth?: number }>
> = {
  ShoppingBasket,
  CupSoda,
  Candy,
  Croissant,
  Milk,
  Carrot,
  Beef,
  SprayCan,
  ShowerHead,
  Brush,
  Baby,
  PencilRuler,
  Hammer,
  Smartphone,
  Package,
  Shirt,
  Shapes,
};

export function CategoryIcon({
  category,
  name,
  size = 20,
  color,
  strokeWidth = 1.8,
}: {
  category: ProductCategory | string;
  /** Server-supplied lucide name (FeedCategory.icon). Preferred when it
   *  resolves, so the server can change a category's icon without an app
   *  release; ignored when it does not, so a typo or an unknown glyph
   *  degrades to the app's own map rather than rendering a hole. */
  name?: string | null;
  size?: number;
  color?: string;
  strokeWidth?: number;
}) {
  const Icon =
    (name ? ICONS_BY_NAME[name] : undefined) ??
    // A category the app does not know yet (backend ahead of a release)
    // falls back to OTHER rather than rendering nothing.
    CATEGORY_ICONS[category as ProductCategory] ??
    CATEGORY_ICONS.OTHER;
  return <Icon size={size} color={color} strokeWidth={strokeWidth} />;
}
