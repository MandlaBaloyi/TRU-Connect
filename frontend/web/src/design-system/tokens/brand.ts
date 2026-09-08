/**
 * TruConnect brand tokens for the web.
 *
 * DELIBERATELY MIRRORS frontend/mobile/src/theme/colors.ts rather than
 * importing from it. A React Native app and a Next app cannot share a
 * TypeScript module without extracting a package, and a package is not
 * worth its weight for nine hex values that change once a year.
 *
 * The same discipline the backend already applies to row_validator.py,
 * which mirrors the frontend's rowValidator.ts field-for-field on
 * purpose: two copies, kept in sync by hand, because the alternative is
 * machinery in service of nothing.
 *
 * IF YOU CHANGE A COLOUR HERE, change it in the mobile theme too.
 * Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 5.
 */

export const brand = {
  /** TruePoint Blue. Primary. Headings, buttons, the "Tru" wordmark. */
  blue: "#0B2447",
  blueLight: "#19376D",
  blueDark: "#051230",

  /** Emerald. Secondary. Accents and the italic "Connect" wordmark. */
  green: "#0FA968",
  greenLight: "#3FCB8C",
  greenDark: "#0A7A4C",

  ink: "#111417",
  inkMuted: "#6B7280",
  line: "#D0D4D9",
  wash: "#F4F6F8",
  white: "#FFFFFF",
} as const;

/**
 * The public marketing site is deliberately ONE audience wide.
 *
 * Businesses do not get a web surface -- they have their phone on them
 * all day and their problem does not require a desk (V2_00 section 2.9).
 * So every call-to-action on this site resolves to one of exactly two
 * places: download the app, or sign in as a supplier. Anything else is a
 * route we would have to justify.
 */
export const APP_STORE_URL = "#";
export const PLAY_STORE_URL = "#";
