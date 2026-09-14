import type { ProductCategory } from "./types";

/**
 * A short line under a category heading, saying what is actually in it.
 *
 * WHY THIS EXISTS. A supplier's profile used to head its strips with
 * the word "Products" and then the category name -- "Products",
 * "Personal Care", "Beverages". The first was empty (everything on the
 * screen is products) and the rest were bare labels doing no work. We
 * KNOW what each category contains, so the heading can say it.
 *
 * IT ALSO SETS EXPECTATIONS BEFORE THE SCROLL. A strip shows six
 * items out of forty; "Cold drinks, water, juice and mixers" tells a
 * business what else is behind it without them having to swipe to find
 * out, which matters most for the categories whose names are vague on
 * their own ("Other", "Hardware & General").
 *
 * DESCRIPTIVE, NEVER PROMOTIONAL. These are not marketing copy and
 * must not become it -- a supplier's actual range is what it is, and a
 * platform-written line claiming "the best in fresh produce" would be
 * TruConnect making a promise on a supplier's behalf that it cannot
 * keep. Each line names the kinds of thing in the category and stops.
 */
export const CATEGORY_DESCRIPTIONS: Record<ProductCategory, string> = {
  FOOD_GROCERY: "Maize meal, rice, oil, tinned food and cupboard staples",
  BEVERAGES: "Cold drinks, water, juice and mixers",
  SNACKS_CONFECTIONERY: "Chips, sweets, chocolates and biscuits",
  BAKERY: "Bread, rolls, flour and baking supplies",
  DAIRY_CHILLED: "Milk, cheese, margarine and chilled goods",
  FRESH_PRODUCE: "Fruit, vegetables and fresh produce by the bag or crate",
  MEAT_FROZEN: "Meat, poultry and frozen goods",
  HOUSEHOLD_CLEANING: "Washing powder, soap, cleaners and household basics",
  PERSONAL_CARE: "Toiletries, soap, fragrance and personal hygiene",
  BEAUTY_HAIR: "Hair pieces, braids, relaxers, cosmetics and nails",
  BABY_FAMILY: "Nappies, formula, baby food and family care",
  STATIONERY_SCHOOL: "Pens, books, school supplies and office basics",
  HARDWARE_GENERAL: "Tools, batteries, globes and general hardware",
  ELECTRONICS_ACCESSORIES: "Airtime, chargers, cables and small electronics",
  PACKAGING_DISPOSABLE: "Bags, containers, cups and disposables",
  CLOTHING_APPAREL: "Clothing, footwear and accessories",
  OTHER: "Everything else this supplier stocks",
};

/** Null rather than a guess for a category this build has not been
 *  told about -- the backend can add one before the app knows it, and
 *  a missing subtitle is better than an invented one. */
export function categoryDescription(category: string): string | null {
  return CATEGORY_DESCRIPTIONS[category as ProductCategory] ?? null;
}
