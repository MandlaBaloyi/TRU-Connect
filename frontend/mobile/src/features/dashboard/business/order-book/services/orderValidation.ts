/**
 * Order Book — input validation. Pure functions, no I/O, so the same
 * rules can run client-side (instant feedback) and will be mirrored
 * server-side (never trusted from the client alone) once the real API
 * exists — same discipline as loan-book/services/loanValidation.ts.
 */

export function validateCustomerName(name: string): string | null {
  const trimmed = name.trim();
  if (trimmed.length === 0) return "Enter a customer name.";
  if (trimmed.length < 2) return "Name is too short.";
  if (trimmed.length > 80) return "Name is too long.";
  return null;
}

export function normalisePhone(phone: string): string {
  return phone.replace(/[^\d+]/g, "");
}

export function validateLineItemDescription(description: string): string | null {
  if (description.trim().length === 0) return "Describe what was ordered.";
  return null;
}

export function validateQuantity(quantity: number | null): string | null {
  if (quantity === null || Number.isNaN(quantity)) return "Enter a quantity.";
  if (quantity <= 0) return "Quantity must be at least 1.";
  if (!Number.isInteger(quantity)) return "Quantity must be a whole number.";
  return null;
}

export function validateUnitPrice(unitPriceCents: number | null): string | null {
  if (unitPriceCents === null) return "Enter a price.";
  if (unitPriceCents < 0) return "Price can't be negative.";
  return null;
}
