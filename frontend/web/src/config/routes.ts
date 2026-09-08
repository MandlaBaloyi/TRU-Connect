/**
 * Every internal path in one place.
 *
 * A route typo is a 404 a reviewer will not catch and a test will not
 * fail on. Referencing paths through this object turns that into a
 * compile error instead -- and when a route moves, it moves once.
 */
export const routes = {
  home: "/",
  suppliers: "/suppliers",
  howItWorks: "/how-it-works",
  pricing: "/pricing",
  about: "/about",
  contact: "/contact",
  terms: "/terms",
  privacy: "/privacy",

  signIn: "/sign-in",
  signUp: "/sign-up",

  portal: {
    dashboard: "/dashboard",
    catalogue: "/catalogue",
    imports: "/imports",
    orders: "/orders",
    storefront: "/storefront",
    profile: "/profile",
    integrations: "/integrations",
    settings: "/settings",
  },
} as const;
