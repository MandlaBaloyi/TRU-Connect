/**
 * Loan Book — the ONLY boundary between this feature and its data.
 * Ref: feature spec ("All backend communication must happen ONLY through
 *      loanBookApi.ts. Never call fetch directly from Screens. Never call
 *      apiClient directly from Components.")
 *
 * SWITCHES between two complete implementations at module load, based on
 * EXPO_PUBLIC_USE_MOCK_API:
 *
 *   mockLoanBookApi.ts  -- in-memory fake data, derives balances itself
 *                          from raw entries+payments (used during UI-first
 *                          development, before a real backend existed).
 *   httpLoanBookApi.ts  -- talks to the real Flask backend, TRUSTS its
 *                          already-derived balances (computed there via
 *                          shared.finance) rather than re-deriving them.
 *
 * EVOLVED FROM THE ORIGINAL SINGLE-OBJECT SWAP DESIGN: the original plan
 * was "swap one `repository: LoanRepository` object". That works when
 * every implementation does the SAME derivation over the SAME raw data.
 * It stopped fitting once the real backend started doing that derivation
 * itself, correctly, server-side -- redoing it client-side against a
 * repository-shaped abstraction would mean two places computing the same
 * money math, with a real risk of them silently disagreeing. Switching
 * whole modules, not one object inside one module, keeps "who owns
 * deriving this balance" unambiguous per code path.
 *
 * Every hook, screen, and component imports from THIS file only, and is
 * completely unaware which implementation is actually running.
 */

import * as mockApi from "./mockLoanBookApi";
import * as httpApi from "./httpLoanBookApi";

// Matches this project's existing convention exactly (see .env's own
// comment): "false = use the real backend. Any other value (including
// missing) leaves the app in mock mode returning fake data."
//
// MUST be this exact literal expression, `process.env.EXPO_PUBLIC_X` --
// Expo's babel plugin does a STATIC TEXT REPLACEMENT at build time,
// swapping this precise expression for the real value. It does NOT
// provide a real, dynamically-queryable process.env object at runtime.
// Any rewritten/indirect form of this expression (a helper function,
// a computed lookup, destructuring) will NOT be recognized by babel's
// static scanner and will silently always read as undefined.
const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const impl = USE_MOCK ? mockApi : httpApi;

export const getLoanBookSummary = impl.getLoanBookSummary;
export const getLoanEntries = impl.getLoanEntries;
export const getLoanEntry = impl.getLoanEntry;
export const getCustomerView = impl.getCustomerView;
export const getCustomerViews = impl.getCustomerViews;
export const listCustomers = impl.listCustomers;
export const searchCustomers = impl.searchCustomers;
export const recordCreditSale = impl.recordCreditSale;
export const recordPayment = impl.recordPayment;
export const deleteLoanEntry = impl.deleteLoanEntry;
export const restoreLoanEntry = impl.restoreLoanEntry;
export const deleteCustomer = impl.deleteCustomer;
export const restoreCustomer = impl.restoreCustomer;
export const deletePayment = impl.deletePayment;
export const getTrash = impl.getTrash;
export const getLoanHistory = impl.getLoanHistory;
export const recordReceiptEvent = impl.recordReceiptEvent;

// LoanBookError is a type/class the mock path defines and some UI code
// may still import from here for its `code` property on failures --
// re-exported so nothing importing it from this file breaks regardless
// of which implementation is active.
export { LoanBookError } from "./mockLoanBookApi";