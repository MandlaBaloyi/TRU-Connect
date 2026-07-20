/**
 * Shared validation patterns.
 * Ref:
 * docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt
 * Sections 1-2 (Business & Supplier Registration)
 */

// ======================================================
// South African Identification
// ======================================================

// South African ID Number
// Format: YYMMDD SSSS C A Z (13 digits)
export const SA_ID_NUMBER_REGEX = /^\d{13}$/;

// South African Mobile Number
// Examples:
// 0821234567
// +27821234567
export const SA_MOBILE_NUMBER_REGEX = /^(?:\+27|0)[6-8][0-9]{8}$/;

// ======================================================
// Email
// ======================================================

export const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// ======================================================
// Password
// ======================================================

/**
 * Password Requirements
 *
 * ✓ Minimum 8 characters
 * ✓ At least one uppercase letter
 * ✓ At least one lowercase letter
 * ✓ At least one number
 * ✓ At least one special character
 */

export const PASSWORD_REGEX =
  /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&.#^()_\-+=])[A-Za-z\d@$!%*?&.#^()_\-+=]{8,}$/;