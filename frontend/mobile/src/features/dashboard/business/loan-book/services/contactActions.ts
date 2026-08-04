/**
 * Loan Book — contact action URL builders. PURE.
 *
 * Deliberately no third-party dependency: `tel:` and `wa.me` are plain
 * URL schemes, opened via React Native's built-in `Linking` module
 * (a thin wrapper, in the hook below) — nothing new to install for
 * either the phone call or WhatsApp action.
 */

import { normalisePhone } from "./loanValidation";

/**
 * `tel:` accepts the number largely as-is; the OS dialer normalises
 * formatting itself. Still routed through normalisePhone() first so a
 * customer stored as "082 123 4567" and one stored as "0821234567"
 * produce an identical, already-validated link.
 */
export function buildTelUrl(phone: string): string {
  return `tel:${normalisePhone(phone)}`;
}

/**
 * wa.me requires INTERNATIONAL digits only — no "+", no leading "0",
 * no spaces or dashes. A South African local number (0821234567) must
 * become 27821234567. Getting this wrong means the link opens WhatsApp
 * to an empty chat instead of the right contact, which looks like the
 * feature is broken rather than like a wrong number.
 */
export function toWhatsAppDigits(phone: string): string {
  const normalised = normalisePhone(phone); // e.g. "0821234567"
  if (normalised.startsWith("0")) {
    return `27${normalised.slice(1)}`;
  }
  return normalised.replace(/\D/g, "");
}

/**
 * wa.me link, optionally pre-filling a message. Using wa.me (not the
 * `whatsapp://` app-scheme) deliberately: wa.me degrades gracefully —
 * opens the app if installed, falls back to a web/App-Store page if
 * not — whereas the raw app-scheme URL just fails silently with no
 * fallback if WhatsApp isn't installed.
 */
export function buildWhatsAppUrl(phone: string, message?: string): string {
  const digits = toWhatsAppDigits(phone);
  const base = `https://wa.me/${digits}`;
  return message ? `${base}?text=${encodeURIComponent(message)}` : base;
}

/** Default WhatsApp message when opening from a loan entry — gives the
 *  customer immediate context rather than an unexplained blank chat. */
export function buildDefaultLoanMessage(customerName: string, amountFormatted: string): string {
  return `Hi ${customerName}, this is a reminder about ${amountFormatted} still owing.`;
}
