/**
 * Settings — the complete information architecture for TruConnect's
 * app preferences.
 *
 * THREE HONEST STATES, never blurred (see SettingStatus below). The
 * hard rule this feature is built around: TruConnect must never
 * present a control as functional when changing it does not actually
 * affect application behaviour. A switch that flips and silently saves
 * a value nothing reads is worse than no switch at all — the business
 * owner walks away believing they configured something they didn't.
 * So a setting is either genuinely wired up (REAL), explains an
 * existing capability without pretending it's configurable
 * (INFORMATIONAL), or is a navigable row leading to an honest
 * explanation (COMING_SOON). Nothing in between.
 */

export type SettingStatus =
  /** Frontend genuinely implements and persists this today. Renders as
   *  a real control (switch/selector) that actually changes app
   *  behaviour. */
  | "REAL"
  /** Explains a capability the app already has, without implying the
   *  user can configure infrastructure that doesn't exist yet.
   *  Renders as a navigable row leading to an explanation screen. */
  | "INFORMATIONAL"
  /** Has a proper Settings entry + explanatory screen, but the
   *  functionality isn't built. Renders as a navigable row — NEVER as
   *  a switch. */
  | "COMING_SOON";

// ---------------------------------------------------------------------------
// The REAL settings — the only ones with persisted values, because they
// are the only ones that currently change anything.
// ---------------------------------------------------------------------------

export type ThemePreference = "SYSTEM" | "LIGHT" | "DARK";

export const THEME_LABELS: Record<ThemePreference, string> = {
  SYSTEM: "System default",
  LIGHT: "Light",
  DARK: "Dark",
};

/** Language is architected for localisation from the start, but only
 *  English is actually available — the rest are listed in the spec as
 *  the eventual target, and would be dishonest to offer as selectable
 *  before any translations exist. See LANGUAGE_LABELS' own note. */
export type LanguagePreference = "EN";

export const LANGUAGE_LABELS: Record<LanguagePreference, string> = {
  EN: "English",
};

/** The eventual set — all 11 of South Africa's official languages
 *  besides English — shown on the Language screen as "coming soon"
 *  rather than as selectable options that would silently do nothing.
 *  Adding a real translation later means moving one entry from here
 *  into LanguagePreference/LANGUAGE_LABELS above — an additive change,
 *  not a restructure. */
export const PLANNED_LANGUAGES: string[] = [
  "Afrikaans",
  "isiZulu",
  "isiXhosa",
  "Sepedi",
  "Setswana",
  "Sesotho",
  "Xitsonga",
  "siSwati",
  "Tshivenda",
  "isiNdebele",
];

/** Which screen TruConnect opens on. Deliberately limited to the
 *  actual primary tabs plus the two business tools that a shop owner
 *  might genuinely live in all day — matching the spec's own list. */
export type StartScreenPreference = "HOME" | "ACCOUNT" | "LOAN_BOOK" | "ORDER_BOOK" | "COMMUNITY" | "DISCOVERY";

export const START_SCREEN_LABELS: Record<StartScreenPreference, string> = {
  HOME: "Home",
  ACCOUNT: "Account",
  LOAN_BOOK: "Loan Book",
  ORDER_BOOK: "Order Book",
  COMMUNITY: "Community",
  DISCOVERY: "Discovery",
};

/** Real routes each start-screen option maps to. Kept beside the
 *  labels so adding an option can't silently forget its destination. */
export const START_SCREEN_ROUTES: Record<StartScreenPreference, string> = {
  HOME: "/business/home",
  ACCOUNT: "/business/account",
  LOAN_BOOK: "/business/loan-book",
  ORDER_BOOK: "/business/order-book",
  COMMUNITY: "/business/community",
  DISCOVERY: "/business/discovery",
};

export interface AppSettings {
  theme: ThemePreference;
  language: LanguagePreference;
  startScreen: StartScreenPreference;
  /** Whether destructive actions ask for confirmation first. Defaults
   *  ON — these are business records, and the spec is explicit that
   *  this only controls the EXTRA confirmation prompt; it never
   *  overrides the backend's own data-integrity rules. */
  confirmBeforeDeleting: boolean;
}

export const DEFAULT_SETTINGS: AppSettings = {
  theme: "SYSTEM",
  language: "EN",
  startScreen: "HOME",
  confirmBeforeDeleting: true,
};
