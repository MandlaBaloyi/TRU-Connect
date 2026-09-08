import type { SupplierProduct } from "../types";
import type { SupplierStorefront } from "./types";

/**
 * A supplier's merchandised storefront, mocked.
 *
 * Same approach, and the same reasoning, as the Community feed's own
 * mock: there is no endpoint for this yet, and writing a ranking
 * service against a screen nobody has looked at is the wrong order to
 * do things in. This lets the sections be built, put on a phone and
 * argued about first.
 *
 * DELIBERATELY INCLUDES THE AWKWARD CASES, same as the feed mock -- a
 * product with no photo, one out of stock, one sold as Each (so the
 * per-unit price has nothing to divide by and must render nothing
 * rather than a fake number), and names long enough to wrap onto two
 * lines. A design that only survives tidy data is not finished.
 */

const IMG = (id: string, w = 400) => `https://images.unsplash.com/${id}?w=${w}&q=70&auto=format&fit=crop`;

const product = (
  id: string,
  name: string,
  priceCents: number,
  imageId: string | null,
  extra: Partial<SupplierProduct> = {}
): SupplierProduct =>
  ({
    id,
    name,
    category: "BEVERAGES",
    priceCents,
    compareAtPriceCents: null,
    sellingUnit: "EACH",
    unitQuantity: null,
    unitMeasure: null,
    inStock: true,
    images: imageId ? [IMG(imageId, 300)] : [],
    ...extra,
  }) as SupplierProduct;

export const MOCK_SUPPLIER_STOREFRONT: SupplierStorefront = {
  sections: [
    {
      id: "featured",
      type: "FEATURED_PRODUCT",
      label: "Supplier's pick",
      product: product("sf-1", "Coca-Cola 2L (case of 6)", 14_400, "photo-1554866585-cd94860890b7", {
        compareAtPriceCents: 17_400,
        sellingUnit: "CASE",
        unitQuantity: 6,
        unitMeasure: "BOTTLE",
      }),
    },

    {
      id: "on-sale",
      type: "ON_SALE",
      title: "On sale now",
      subtitle: "Prices drop back on Monday",
      products: [
        product("sf-2", "Fanta Orange 2L (case of 6)", 12_900, "photo-1624517452488-04869289c4ca", {
          compareAtPriceCents: 15_600,
          sellingUnit: "CASE",
          unitQuantity: 6,
          unitMeasure: "BOTTLE",
        }),
        product("sf-3", "Stoney Ginger Beer 2L (case of 6)", 13_200, "photo-1613478223719-2ab802602423", {
          compareAtPriceCents: 15_000,
          sellingUnit: "CASE",
          unitQuantity: 6,
          unitMeasure: "BOTTLE",
        }),
        // NO PHOTO, still on sale. The ribbon has to sit correctly on
        // the fallback block too.
        product("sf-4", "Sprite 500ml (case of 24)", 18_900, null, {
          compareAtPriceCents: 22_000,
          sellingUnit: "CASE",
          unitQuantity: 24,
          unitMeasure: "BOTTLE",
        }),
        product("sf-5", "Bonaqua Still Water 500ml (case of 24)", 9_600, "photo-1560023907-5f339617ea30", {
          compareAtPriceCents: 11_500,
          sellingUnit: "CASE",
          unitQuantity: 24,
          unitMeasure: "BOTTLE",
        }),
      ],
    },

    {
      id: "best-sellers",
      type: "BEST_SELLERS",
      title: "What businesses buy most",
      subtitle: "Ordered most in the last 30 days",
      products: [
        product("sf-6", "Coca-Cola 2L (case of 6)", 14_400, "photo-1554866585-cd94860890b7", {
          sellingUnit: "CASE",
          unitQuantity: 6,
          unitMeasure: "BOTTLE",
        }),
        product("sf-7", "White Star Super Maize Meal 10kg", 12_500, "photo-1586201375761-83865001e31c", {
          sellingUnit: "BAG",
        }),
        product("sf-8", "Sunlight Dishwashing Liquid 750ml", 3_299, "photo-1585421514738-01798e348b17"),
        // OUT OF STOCK but still a best seller -- popularity and
        // availability are different facts and the card must say so.
        product("sf-9", "Blue Ribbon Bread (case of 12)", 15_600, "photo-1509440159596-0249088772ff", {
          sellingUnit: "CASE",
          unitQuantity: 12,
          unitMeasure: "EACH",
          inStock: false,
        }),
        product("sf-10", "Joko Tagless Teabags 100s", 4_150, "photo-1597318181409-cf64d0b5d8a2"),
      ],
    },

    {
      id: "new-arrivals",
      type: "NEW_ARRIVALS",
      title: "Just added",
      subtitle: "New from this supplier",
      products: [
        product("sf-15", "Rhodes Tomato Sauce 700ml", 4_899, "photo-1613145997970-db84a7975fbb"),
        product("sf-16", "Maq Washing Powder 2kg", 8_950, "photo-1585421514738-01798e348b17", {
          sellingUnit: "BAG",
        }),
        product("sf-17", "Clover Fresh Milk 2L (case of 6)", 13_800, "photo-1550583724-b2692b85b150", {
          sellingUnit: "CASE",
          unitQuantity: 6,
          unitMeasure: "BOTTLE",
        }),
        product("sf-18", "Lucky Star Pilchards 400g (box of 12)", 22_400, null, {
          sellingUnit: "BOX",
          unitQuantity: 12,
          unitMeasure: "EACH",
        }),
      ],
    },

    // THE SUPPLIER'S OWN SELECTION, titled by them. Month-end is the
    // single biggest rhythm in South African informal retail -- payday
    // buying is a genuinely different basket from mid-month -- and it
    // is the kind of judgement only the person selling can make.
    {
      id: "curated-month-end",
      type: "CURATED",
      title: "Stock up for month-end",
      subtitle: "What sells out first after payday",
      products: [
        product("sf-19", "Coca-Cola 2L (case of 6)", 14_400, "photo-1554866585-cd94860890b7", {
          sellingUnit: "CASE",
          unitQuantity: 6,
          unitMeasure: "BOTTLE",
        }),
        product("sf-20", "Simba Chips 36g (box of 48)", 24_000, "photo-1566478989037-eec170784d0b", {
          sellingUnit: "BOX",
          unitQuantity: 48,
          unitMeasure: "PACKET",
        }),
        product("sf-21", "White Star Super Maize Meal 10kg", 12_500, "photo-1586201375761-83865001e31c", {
          sellingUnit: "BAG",
        }),
      ],
    },

    {
      id: "bulk",
      type: "BULK_VALUE",
      title: "Better per unit in bulk",
      subtitle: "The more in the pack, the less each one costs",
      products: [
        product("sf-11", "Coca-Cola 330ml (case of 24)", 21_600, "photo-1554866585-cd94860890b7", {
          sellingUnit: "CASE",
          unitQuantity: 24,
          unitMeasure: "CAN",
        }),
        product("sf-12", "Simba Chips 36g (box of 48)", 24_000, "photo-1566478989037-eec170784d0b", {
          sellingUnit: "BOX",
          unitQuantity: 48,
          unitMeasure: "PACKET",
        }),
        product("sf-13", "Sunlight Soap 175g (box of 20)", 18_000, "photo-1585421514738-01798e348b17", {
          sellingUnit: "BOX",
          unitQuantity: 20,
          unitMeasure: "EACH",
        }),
        // SOLD AS EACH -- nothing to divide by, so the per-unit line
        // must render NOTHING rather than repeating the pack price.
        product("sf-14", "Sunflower Oil 5L", 19_900, "photo-1474979266404-7eaacbcd87c5"),
      ],
    },
  ],
};
