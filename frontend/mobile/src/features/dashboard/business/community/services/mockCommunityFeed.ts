import type { CommunityFeed, FeedProduct, FeedSupplier } from "../types";

/**
 * The Community feed, mocked.
 *
 * WHY THIS EXISTS AT ALL, when most of the Community tab already talks
 * to a real backend: there is no feed endpoint yet, and building one
 * before the design is settled would mean writing a ranking service
 * against a screen nobody has looked at. This lets the whole screen be
 * built, put on a real phone, and argued about first. The http service
 * then swaps in behind the identical interface -- the same
 * mock/http split mockSupplierSearchService already uses.
 *
 * DELIBERATELY REALISTIC, not "Lorem Supplier 1". Placeholder data
 * makes a design look better than it is: every name the same length,
 * every price four digits, every card with a photo. Real South African
 * wholesaler names, real spaza stock, real prices in cents, and --
 * importantly -- the awkward cases mixed in on purpose:
 *
 *   * a supplier with NO cover image and no logo (initials fallback)
 *   * a product with no photo
 *   * a supplier who has never stated delivery terms (null, not false)
 *   * a supplier with no minimum order
 *   * a business name long enough to truncate
 *   * an out-of-stock product
 *   * distanceKm null on some, as the http service will return it
 *
 * If the screen still looks right with those in it, it will survive
 * contact with the real catalogue. If it only looks right with perfect
 * data, it is not finished.
 */

// Photos come from Unsplash's own CDN rather than being bundled: this
// file is throwaway, and committing a dozen images for a mock would
// outlive its usefulness in the repo. They also make the data-cost
// question real while designing -- see the note in the plan about
// image sizing mattering more here than in most apps.
const IMG = (id: string, w = 400) => `https://images.unsplash.com/${id}?w=${w}&q=70&auto=format&fit=crop`;

const macman: FeedSupplier = {
  id: "sup-macman",
  businessName: "MacMan Businesses",
  businessImageUrl: IMG("photo-1580913428735-bd3c269d6a82", 200),
  coverImageUrl: IMG("photo-1550989460-0adf9ea622e2"),
  category: "Wholesale beverages",
  location: "Soweto",
  verificationStatus: "unverified",
  offersDelivery: true,
  minimumOrderCents: 50_000,
  connectedBusinessCount: 6,
  lastActiveAt: new Date(Date.now() - 3 * 60 * 1000).toISOString(),
  isConnected: true,
  distanceKm: 4.2,
};

const thabo: FeedSupplier = {
  id: "sup-thabo",
  businessName: "Thabo Fresh Produce",
  businessImageUrl: IMG("photo-1542838132-92c53300491e", 200),
  coverImageUrl: IMG("photo-1488459716781-31db52582fe9"),
  category: "Fruit & vegetables",
  location: "Mamelodi",
  verificationStatus: "unverified",
  offersDelivery: true,
  minimumOrderCents: 30_000,
  connectedBusinessCount: 14,
  lastActiveAt: new Date(Date.now() - 40 * 60 * 1000).toISOString(),
  isConnected: true,
  distanceKm: 7.8,
};

// NO IMAGES AT ALL, and no delivery terms stated. The initials
// fallback and the missing-delivery case both have to look deliberate.
const nomvula: FeedSupplier = {
  id: "sup-nomvula",
  businessName: "Nomvula Cash & Carry Wholesalers",
  businessImageUrl: null,
  coverImageUrl: null,
  category: "General groceries",
  location: "Tembisa",
  verificationStatus: "unverified",
  offersDelivery: null,
  minimumOrderCents: null,
  connectedBusinessCount: 2,
  lastActiveAt: null,
  isConnected: false,
  distanceKm: 12.5,
};

const kasi: FeedSupplier = {
  id: "sup-kasi",
  businessName: "Kasi Bakery Supplies",
  businessImageUrl: IMG("photo-1509440159596-0249088772ff", 200),
  coverImageUrl: IMG("photo-1486427944299-d1955d23e34d"),
  category: "Bakery & dry goods",
  location: "Katlehong",
  verificationStatus: "verified",
  offersDelivery: false,
  minimumOrderCents: 20_000,
  connectedBusinessCount: 31,
  lastActiveAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  isConnected: false,
  distanceKm: null,
};

const zenzele: FeedSupplier = {
  id: "sup-zenzele",
  businessName: "Zenzele Meat Distributors",
  businessImageUrl: IMG("photo-1607623814075-e51df1bdc82f", 200),
  coverImageUrl: IMG("photo-1607623814075-e51df1bdc82f"),
  category: "Meat & poultry",
  location: "Alexandra",
  verificationStatus: "unverified",
  offersDelivery: true,
  minimumOrderCents: 100_000,
  connectedBusinessCount: 9,
  lastActiveAt: new Date(Date.now() - 20 * 60 * 60 * 1000).toISOString(),
  isConnected: false,
  distanceKm: 2.1,
};

const product = (
  id: string,
  supplier: FeedSupplier,
  name: string,
  priceCents: number,
  imageId: string | null,
  extra: Partial<FeedProduct> = {}
): FeedProduct => ({
  id,
  supplierId: supplier.id,
  supplierName: supplier.businessName,
  name,
  imageUrl: imageId ? IMG(imageId, 300) : null,
  priceCents,
  compareAtPriceCents: null,
  unitLabel: "each",
  inStock: true,
  // A PLAUSIBLE DEFAULT, overridable per product. Mock mode exists to
  // show the real shape of a screen, and a mock with no social proof
  // would have hidden the badge entirely during UI work.
  buyerCount: 4,
  buyerLabel: "4 businesses bought this",
  ...extra,
});

export const MOCK_COMMUNITY_FEED: CommunityFeed = {
  sections: [
    {
      id: "chips",
      type: "CATEGORY_CHIPS",
      categories: [
        { value: "BEVERAGES", label: "Drinks", icon: "CupSoda" },
        { value: "FOOD", label: "Food", icon: "Beef" },
        { value: "FRUIT_VEG", label: "Fruit & veg", icon: "Carrot" },
        { value: "BAKERY", label: "Bakery", icon: "Croissant" },
        { value: "CLEANING", label: "Cleaning", icon: "SprayCan" },
        { value: "OTHER", label: "More", icon: "Package" },
      ],
    },

    // BUY IT AGAIN LEADS, and that placement is the whole argument for
    // this screen. A business coming here usually already knows what
    // they need; the fastest possible path to re-ordering it beats any
    // amount of discovery below. The endpoint for this is already
    // built and tested and renders nowhere in the app today.
    {
      id: "buy-again",
      type: "PRODUCT_RAIL",
      title: "Buy it again",
      subtitle: "From your last orders",
      products: [
        product("p-1", macman, "Coca-Cola 2L", 2_499, "photo-1554866585-cd94860890b7", {
          compareAtPriceCents: 2_899,
        }),
        product("p-2", macman, "Fanta Orange 2L", 2_299, "photo-1624517452488-04869289c4ca"),
        product("p-3", thabo, "Potatoes 10kg bag", 8_999, "photo-1518977676601-b53f82aba655", {
          unitLabel: "10kg bag",
        }),
        product("p-4", thabo, "Onions 7kg bag", 6_499, "photo-1508747703725-719777637510", {
          unitLabel: "7kg bag",
        }),
        product("p-5", kasi, "White bread flour 12.5kg", 18_500, "photo-1509440159596-0249088772ff", {
          unitLabel: "12.5kg",
        }),
      ],
    },

    {
      id: "your-suppliers",
      type: "SUPPLIER_AVATARS",
      title: "Your suppliers",
      suppliers: [macman, thabo, kasi, zenzele, nomvula],
    },

    {
      id: "near-you",
      type: "SUPPLIER_RAIL",
      title: "Collect near you",
      subtitle: "Closest to Soweto",
      suppliers: [zenzele, macman, thabo, nomvula],
      seeAllHref: null,
    },

    {
      id: "promo-1",
      type: "PROMO",
      promo: {
        title: "Invite a supplier, get them on TruConnect",
        body: "Order from the people you already buy from, without the phone calls.",
        imageUrl: null,
        href: "/business/find-supplier/invite",
      },
    },

    {
      id: "popular",
      type: "PRODUCT_RAIL",
      title: "Moving fast right now",
      subtitle: "Ordered most this week",
      products: [
        product("p-6", zenzele, "Chicken portions 5kg", 34_900, "photo-1604503468506-a8da13d82791", {
          unitLabel: "5kg box",
        }),
        // NO PHOTO -- the fallback has to look deliberate, not broken.
        product("p-7", nomvula, "Sunlight dishwashing liquid 750ml", 3_299, null),
        product("p-8", macman, "Stoney Ginger Beer 2L", 2_399, "photo-1613478223719-2ab802602423"),
        // OUT OF STOCK, deliberately in a "popular" rail -- popularity
        // and availability are different facts and the card must say so.
        product("p-9", kasi, "Blue Ribbon bread (case of 12)", 15_600, "photo-1509440159596-0249088772ff", {
          unitLabel: "case of 12",
          inStock: false,
        }),
        product("p-10", thabo, "Tomatoes 5kg", 7_450, "photo-1592924357228-91a4daadcfea", {
          unitLabel: "5kg",
        }),
      ],
    },

    // NOTHING FILLS THIS IN PRODUCTION YET. It is here so the paid
    // placement design is settled and shipped before the first
    // wholesaler asks for it -- see the type's own comment.
    {
      id: "sponsored-1",
      type: "SPONSORED_SUPPLIER",
      label: "Sponsored",
      supplier: kasi,
    },

    {
      id: "new-to-you",
      type: "SUPPLIER_RAIL",
      title: "Suppliers you haven't ordered from",
      subtitle: "Connected, but no orders yet",
      suppliers: [nomvula, kasi, zenzele],
      seeAllHref: null,
    },
  ],
};
