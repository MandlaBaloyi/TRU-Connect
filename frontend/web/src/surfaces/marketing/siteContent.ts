/**
 * What the public site says, in one place.
 *
 * SEPARATED FROM THE COMPONENTS because copy changes far more often
 * than layout does, and because it is the part a non-engineer should be
 * able to read and correct. A marketing claim buried in JSX is a claim
 * nobody reviews.
 *
 * ─────────────────────────────────────────────────────────────────────
 * THE RULE THIS FILE EXISTS TO ENFORCE: NOTHING HERE MAY BE ASPIRATIONAL.
 *
 * A real company's site has slots for customer logos, headline metrics
 * and analyst badges. TruConnect has not earned any of those yet, and
 * filling those slots with invented numbers is the single fastest way to
 * lose a wholesaler who checks. So the STRUCTURE is that of a real
 * company site and the CONTENT is only what is true today.
 *
 * Where a competitor would put "13,000 brands", this site puts what it
 * actually has: how the thing works, what it costs, and who to call.
 * That is not a weaker page -- for a buyer evaluating a young platform
 * it is a more credible one.
 * ─────────────────────────────────────────────────────────────────────
 */

/** Fill this in and the contact page stops saying it has no address. */
export const CONTACT_EMAIL = "";
export const SALES_EMAIL = "";

/**
 * The supplier plans, straight from the backend's own tier limits
 * (supplier/order_limits/tiers/*.py). These caps are REAL and enforced
 * in code -- they are not marketing numbers.
 *
 * PRICES ARE DELIBERATELY ABSENT. There is no price on a tier anywhere
 * in the system, because none has been set. Inventing one for the page
 * would be the worst kind of lie: the sort a supplier only discovers
 * after they have committed. "Talk to us" is the honest answer while
 * pricing is genuinely undecided, and it is what most B2B platforms do
 * at this stage anyway.
 */
export const SUPPLIER_PLANS = [
  {
    name: "Starter",
    tier: "FREE",
    forWho: "A trader or small wholesaler getting listed.",
    price: "Free",
    priceNote: "No card needed",
    directCap: "R10,000",
    features: [
      "List your products with real prices",
      "Take orders from businesses on TruConnect",
      "Set your own minimum order and delivery terms",
      "Accept or decline every order yourself",
    ],
    cta: "Create an account",
    highlight: false,
  },
  {
    name: "Growth",
    tier: "PRO",
    forWho: "A wholesaler supplying regularly, with a real catalogue.",
    price: "Talk to us",
    priceNote: "Pricing is being set with our first suppliers",
    directCap: "R25,000",
    features: [
      "Everything in Starter",
      "Upload your whole catalogue from a spreadsheet",
      "Re-upload your price file weekly — it updates, never duplicates",
      "Choose what appears at the top of your shopfront",
    ],
    cta: "Talk to sales",
    highlight: true,
  },
  {
    name: "Scale",
    tier: "MAX",
    forWho: "A regional distributor running their own system.",
    price: "Talk to us",
    priceNote: "Includes onboarding support",
    directCap: "R50,000",
    features: [
      "Everything in Growth",
      "Connect your own system directly",
      "Orders arrive without anyone approving them one by one",
      "A person you can call",
    ],
    cta: "Talk to sales",
    highlight: false,
  },
] as const;

/**
 * How a supplier's catalogue actually reaches TruConnect.
 *
 * THIS IS THE SECTION A BIG SUPPLIER READS FIRST, and it is TruConnect's
 * honest equivalent of a competitor's "connects to your tech stack"
 * page. A wholesaler with 3,000 lines does not care about the app; they
 * care whether they have to retype their catalogue. The answer is no,
 * and this says which door they come through.
 */
export const INGESTION_PATHS = [
  {
    name: "Type it in",
    forWho: "A few dozen products",
    body: "Add products one at a time from your phone. No spreadsheet, no setup, nothing to learn.",
    status: "Available",
  },
  {
    name: "Upload a spreadsheet",
    forWho: "Hundreds to thousands of products",
    body: "Send the price file you already have. Re-upload it whenever prices change and your listings update in place — it never creates duplicates. Include a barcode column and your products are matched to our catalogue instantly.",
    status: "Available",
  },
  {
    name: "Connect your system",
    forWho: "A distributor with their own software",
    body: "Push stock and prices straight from your ERP. No one sits and types, and no one clicks approve on every order.",
    status: "Talk to us",
  },
] as const;

/**
 * What TruConnect can honestly say about itself today. Every line is a
 * property of the product, not a claim about traction -- because there
 * is no traction to claim yet, and a young platform that says so is
 * more trustworthy than one that pads.
 */
export const PLATFORM_FACTS = [
  {
    label: "Built for South Africa",
    body: "Spaza shops, salons and small retailers — and the wholesalers who already supply them.",
  },
  {
    label: "Your terms, not ours",
    body: "Minimum order, delivery or collection, which payments you take, what businesses can see. All yours to set.",
  },
  {
    label: "A record on both sides",
    body: "Every order written down the same way for buyer and supplier. No more reconstructing a WhatsApp thread.",
  },
] as const;

/** The problems the platform exists to solve, in the buyer's words. */
export const PROBLEMS = [
  {
    title: "Orders live in WhatsApp",
    body: "A voice note, three photos and a phone call. Nobody can find what was agreed a week later, and neither side has a record when it goes wrong.",
  },
  {
    title: "Prices move without warning",
    body: "You find out the case price changed when the invoice arrives. Comparing two suppliers means remembering what each of them said.",
  },
  {
    title: "Stock runs out quietly",
    body: "You order, then wait, then find out it was never in stock. The trip is wasted and the shelf stays empty.",
  },
] as const;
