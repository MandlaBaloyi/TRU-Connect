/**
 * Loan Book — input validation.
 * Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt §12.3,
 *      docs/02_SYSTEM_UI_UX_SPECIFICATION.txt §9 (Forms)
 *
 * Returns result objects rather than throwing, so screens can render
 * inline errors beneath the relevant field (Doc 02 §9) instead of
 * catching exceptions.
 *
 * Messages are plain language, never financial jargon (Doc 02 §14):
 * "Enter how much they owe", not "Principal amount is a required field".
 */

import type { Cents, RecordCreditSaleInput } from "../types";

export interface ValidationResult {
  isValid: boolean;
  /** Field name → message, for rendering beneath the right input. */
  errors: Record<string, string>;
}

const ok: ValidationResult = { isValid: true, errors: {} };

/**
 * Upper bound on a single credit sale: R 100,000.
 *
 * Not a business rule — a typo guard. Entering an amount in cents by
 * mistake (485000 instead of 4850) is an easy slip on a numeric keypad,
 * and an implausible figure sitting in the book is worse than a rejected
 * entry. Deliberately generous so it only catches genuine errors.
 */
export const MAX_SINGLE_SALE_CENTS = 10_000_000;

export function validateCreditSale(input: RecordCreditSaleInput): ValidationResult {
  const errors: Record<string, string> = {};

  // Customer: either an existing one, or a name for a new one.
  if (!input.customerId && !input.newCustomerName?.trim()) {
    errors.customer = "Choose a customer or enter a name.";
  }

  if (input.newCustomerName !== undefined && input.newCustomerName.trim().length === 1) {
    errors.newCustomerName = "Enter the customer's full name.";
  }

  if (input.newCustomerPhone) {
    const phoneError = validatePhone(input.newCustomerPhone);
    if (phoneError) errors.newCustomerPhone = phoneError;
  }

  const amountError = validateAmount(input.amount);
  if (amountError) errors.amount = amountError;

  if (input.saleDate) {
    const saleDate = new Date(input.saleDate);
    if (Number.isNaN(saleDate.getTime())) {
      errors.saleDate = "Choose a valid date.";
    } else if (saleDate.getTime() > Date.now() + 24 * 60 * 60 * 1000) {
      // Allowing a small forward window avoids false rejections from
      // device clock skew or timezone edges, while still catching a
      // genuinely wrong year.
      errors.saleDate = "The sale date can't be in the future.";
    }
  }

  return Object.keys(errors).length > 0 ? { isValid: false, errors } : ok;
}

export function validateAmount(amount: Cents | undefined): string | null {
  if (amount === undefined || amount === null) return "Enter an amount.";
  if (!Number.isInteger(amount)) return "Enter a valid amount.";
  if (amount <= 0) return "Enter an amount greater than zero.";
  if (amount > MAX_SINGLE_SALE_CENTS) return "That amount looks too high. Check and try again.";
  return null;
}

/**
 * South African mobile numbers: 10 digits starting 0, or +27 followed by
 * 9. Spaces, dashes, and brackets are stripped first — people paste
 * numbers from contacts in every conceivable format, and rejecting
 * "082 123 4567" for containing spaces would be needless friction.
 */
export function validatePhone(phone: string): string | null {
  const cleaned = phone.replace(/[\s\-()]/g, "");
  if (cleaned.length === 0) return null; // optional field
  const isLocal = /^0\d{9}$/.test(cleaned);
  const isInternational = /^\+27\d{9}$/.test(cleaned);
  if (!isLocal && !isInternational) return "Enter a valid phone number.";
  return null;
}

export function validateCustomerName(name: string): string | null {
  const trimmed = name.trim();
  if (trimmed.length === 0) return "Enter the customer's name.";
  if (trimmed.length < 2) return "Enter the customer's full name.";
  if (trimmed.length > 100) return "That name is too long.";
  return null;
}

/** Normalises a phone number to a consistent stored form (0XXXXXXXXX),
 *  so duplicate detection by phone works regardless of input format. */
export function normalisePhone(phone: string): string {
  const cleaned = phone.replace(/[\s\-()]/g, "");
  if (cleaned.startsWith("+27")) return `0${cleaned.slice(3)}`;
  return cleaned;
}
