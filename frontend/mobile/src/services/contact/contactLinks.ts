import { Linking } from "react-native";

/**
 * Contact-link builders — PURE, plus one thin Linking wrapper.
 *
 * WHY THESE LIVE IN services/ AND NOT IN A FEATURE: `buildWhatsAppUrl`
 * started life in loan-book (chasing a customer for money owed) and was
 * then imported by my-suppliers, orders, and the product detail screen;
 * `buildTikTokUrl`/`openUrl` started in my-suppliers and are now wanted
 * by find-supplier's brand profile too. Four features reaching
 * sideways into two others for the same handful of URL builders is the
 * shape of something that was never feature-specific to begin with.
 *
 * The move also removes a REAL dependency inversion: find-supplier is
 * the feature my-suppliers depends on (see mockSupplierSearchService's
 * own note on that direction), so find-supplier importing
 * my-suppliers/services/contactActions would have pointed the arrow
 * backwards. Neutral ground, same principle as shared/connections.
 *
 * No third-party dependency: `tel:`, `wa.me` and tiktok.com are plain
 * URLs opened through React Native's built-in Linking.
 */

/**
 * South African local form. Strips spaces/dashes/parens and converts a
 * +27 international prefix back to a leading 0, so "+27 82 123 4567",
 * "082 123 4567" and "0821234567" all normalise identically.
 *
 * Deliberately a copy of loan-book's own normalisePhone rather than an
 * import of it: this module is neutral ground and must not depend on a
 * feature. The two are five lines and describe the same national
 * numbering rule, which is not going to drift.
 */
function normalisePhone(phone: string): string {
  const cleaned = phone.replace(/[\s\-()]/g, "");
  if (cleaned.startsWith("+27")) return `0${cleaned.slice(3)}`;
  return cleaned;
}

/**
 * `tel:` accepts the number largely as-is; the OS dialer normalises
 * formatting itself. Still routed through normalisePhone first so two
 * differently-formatted copies of the same number produce an identical
 * link.
 */
export function buildTelUrl(phone: string): string {
  return `tel:${normalisePhone(phone)}`;
}

/**
 * wa.me requires INTERNATIONAL digits only — no "+", no leading "0",
 * no spaces or dashes. A South African local number (0821234567) must
 * become 27821234567. Getting this wrong opens WhatsApp to an empty
 * chat instead of the right contact, which reads as a broken feature
 * rather than a wrong number.
 */
export function toWhatsAppDigits(phone: string): string {
  const normalised = normalisePhone(phone);
  if (normalised.startsWith("0")) {
    return `27${normalised.slice(1)}`;
  }
  return normalised.replace(/\D/g, "");
}

/**
 * wa.me link, optionally pre-filling a message. Using wa.me (not the
 * `whatsapp://` app-scheme) deliberately: wa.me degrades gracefully —
 * opens the app if installed, falls back to a web/App-Store page if
 * not — whereas the raw app-scheme URL fails silently with no fallback
 * when WhatsApp isn't installed.
 */
export function buildWhatsAppUrl(phone: string, message?: string): string {
  const digits = toWhatsAppDigits(phone);
  const base = `https://wa.me/${digits}`;
  return message ? `${base}?text=${encodeURIComponent(message)}` : base;
}

export function buildTikTokUrl(handle: string): string {
  return `https://www.tiktok.com/@${handle}`;
}

export function buildEmailUrl(email: string): string {
  return `mailto:${email}`;
}

export function openUrl(url: string) {
  Linking.openURL(url).catch(() => {
    // Silently ignored, same reasoning as ContactActionsRow.tsx's own
    // handlers: wa.me and tiktok.com both degrade to a normal web page
    // when the native app isn't installed, so a failure here means no
    // URL at all could be opened (no network route) -- nothing more
    // useful to do than leave the screen as it was.
  });
}
