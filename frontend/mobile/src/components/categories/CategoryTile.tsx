import React from "react";
import { StyleSheet, View } from "react-native";

import { CategoryIcon } from "./CategoryIcon";
import type { ProductCategory } from "@/constants/productCategories";
import { palette } from "@/theme/colors";

/**
 * The coloured square that stands in for a product photograph.
 *
 * FOUR COLOURS, NOT SEVENTEEN. The brand palette is two colours and
 * some semantics; inventing seventeen hues to fill a grid would fight
 * it and look like a children's app. So colour groups the categories
 * and the ICON distinguishes them — a shopper scanning a list sees
 * green for food, blue for the home, purple for the person, amber for
 * everything else, and reads the icon for the rest.
 *
 * Deliberately the SAME four tones as EntityAvatar's initials fallback,
 * so a screen showing supplier avatars beside product tiles looks like
 * one app rather than two.
 *
 * A TILE IS NEVER AN ERROR STATE. Most products have no photograph and
 * always will — a supplier importing four hundred rows from a
 * spreadsheet is not going to photograph them. So this must look like a
 * deliberate design, not a hole where an image failed.
 */

const FOOD = palette.emeraldGreenDark;
const HOME = palette.truePointBlue;
const PERSON = "#6B4E9E";
const GENERAL = "#B45309";

const TILE_COLOUR: Record<ProductCategory, string> = {
  FOOD_GROCERY: FOOD,
  BEVERAGES: FOOD,
  SNACKS_CONFECTIONERY: FOOD,
  BAKERY: FOOD,
  DAIRY_CHILLED: FOOD,
  FRESH_PRODUCE: FOOD,
  MEAT_FROZEN: FOOD,
  HOUSEHOLD_CLEANING: HOME,
  PACKAGING_DISPOSABLE: HOME,
  HARDWARE_GENERAL: HOME,
  PERSONAL_CARE: PERSON,
  BEAUTY_HAIR: PERSON,
  BABY_FAMILY: PERSON,
  CLOTHING_APPAREL: PERSON,
  STATIONERY_SCHOOL: GENERAL,
  ELECTRONICS_ACCESSORIES: GENERAL,
  OTHER: GENERAL,
};

export function colourForCategory(category: ProductCategory | string): string {
  return TILE_COLOUR[category as ProductCategory] ?? GENERAL;
}

export function CategoryTile({
  category,
  size = 56,
  radius = 8,
  fill = false,
}: {
  category: ProductCategory | string;
  size?: number;
  radius?: number;
  /** Fill the parent instead of a fixed square — see CategoryImage. */
  fill?: boolean;
}) {
  const box = fill
    ? ({ width: "100%", height: "100%" } as const)
    : ({ width: size, height: size, borderRadius: radius } as const);

  return (
    <View style={[styles.tile, box, { backgroundColor: colourForCategory(category) }]}>
      <CategoryIcon
        category={category}
        size={fill ? 28 : Math.round(size * 0.42)}
        color={palette.white}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  tile: { alignItems: "center", justifyContent: "center" },
});
