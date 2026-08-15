/**
 * Subscription & Billing — TRU Connect's own platform-usage model.
 * See types.ts's own extensive note: three tiers this round, every
 * account is FREE, hardcoded, no billing infrastructure exists
 * anywhere in this codebase yet. requestUpgrade never actually
 * upgrades anything — it's the same honest "not connected yet"
 * treatment as everywhere else unbuilt backend shows up in this app.
 */
import type { SubscriptionTierInfo, SupplierSubscription } from "../types";

const latency = () => new Promise<void>((resolve) => setTimeout(resolve, 300));

/** PROVISIONAL — see types.ts's own note. These numbers/features are
 *  placeholders reflecting what's been discussed so far, not a final
 *  pricing decision. */
export const SUBSCRIPTION_TIERS: SubscriptionTierInfo[] = [
  {
    tier: "FREE",
    name: "Supplier Free",
    priceLabel: "Free",
    features: [
      "Listed in Find Supplier",
      "Up to 20 orders received per month",
      "Up to 15 products in your catalogue",
      "Standard search ranking",
    ],
    hasWebPortalAccess: false,
  },
  {
    tier: "PRO",
    name: "Supplier Pro",
    priceLabel: "Pricing to be announced",
    features: [
      "Everything in Free",
      "Higher monthly order limit",
      "Larger product catalogue",
      "Priority placement in search results",
      "Web portal access on desktop",
    ],
    hasWebPortalAccess: true,
  },
  {
    tier: "MAX",
    name: "Supplier Max",
    priceLabel: "Pricing to be announced",
    features: [
      "Everything in Pro",
      "Highest monthly order limit",
      "Unlimited product catalogue",
      "Top priority placement in search results",
      "Web portal access on desktop",
    ],
    hasWebPortalAccess: true,
  },
];

let currentSubscription: SupplierSubscription = { tier: "FREE", nextBillingDate: null };

export async function getSubscription(): Promise<SupplierSubscription> {
  await latency();
  return currentSubscription;
}

/** Never actually upgrades anything — see this file's own docstring.
 *  Always throws with an honest, specific reason, matching the same
 *  "Coming soon" discipline Card Payments already established on the
 *  business side rather than silently succeeding. */
export async function requestUpgrade(): Promise<never> {
  await latency();
  throw new Error("Upgrading isn't connected to real billing yet — this is coming in a future update.");
}
