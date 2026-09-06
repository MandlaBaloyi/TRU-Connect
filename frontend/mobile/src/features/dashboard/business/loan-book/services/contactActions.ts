/**
 * Loan Book — the one contact helper that is genuinely loan-specific.
 *
 * The generic URL builders that used to live here (buildTelUrl,
 * toWhatsAppDigits, buildWhatsAppUrl) MOVED to
 * src/services/contact/contactLinks.ts: they had grown four importers
 * across three other features, which made "loan book owns them" wrong.
 * See that module's own docstring for the full reasoning.
 */

/** Default WhatsApp message when opening from a loan entry — gives the
 *  customer immediate context rather than an unexplained blank chat. */
export function buildDefaultLoanMessage(customerName: string, amountFormatted: string): string {
  return `Hi ${customerName}, this is a reminder about ${amountFormatted} still owing.`;
}
