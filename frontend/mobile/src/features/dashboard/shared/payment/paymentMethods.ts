/**
 * How an order gets paid for -- ONE definition, used by both roles.
 *
 * IT LIVED IN TWO PLACES BEFORE THIS, character-for-character identical
 * in business/orders/types.ts and supplier/stock-orders/types.ts. That
 * is the same duplication that just cost the backend a real bug: DIRECT
 * was added to the order enum and the database and to nothing else, so
 * the payment method the platform is supposed to offer could not
 * complete a checkout at all. Two copies of a list is how a value gets
 * added to one of them.
 *
 * DIRECT REPLACED CASH AND PROOF_OF_PAYMENT, and the reasoning is worth
 * keeping close to the type. TruConnect never observed either of them:
 * a buyer who selected proof-of-payment and then handed over notes was
 * indistinguishable from one who transferred. They were never two rails,
 * they were one rail described two ways -- money that moves outside the
 * platform. One name, honestly.
 *
 * THE OLD VALUES STAY IN THE TYPE and are deliberately NOT offered. Real
 * orders recorded what the buyer selected at the time, and rewriting
 * that would be falsifying history rather than correcting it. So they
 * must still RENDER; they must never be SELECTABLE. That split is the
 * whole reason SELECTABLE_PAYMENT_METHODS exists separately from the
 * type.
 */

export type PaymentMethod = "DIRECT" | "CASH" | "PROOF_OF_PAYMENT" | "PAYFAST";

/**
 * What a buyer may actually choose today.
 *
 * PAYFAST IS ABSENT because the gateway is not wired -- offering it
 * would take a business to a checkout that cannot complete. CASH and
 * PROOF_OF_PAYMENT are absent because DIRECT is what they became.
 *
 * Derived from, not duplicated into, the picker on
 * DeliveryPaymentScreen -- adding a method there means adding it here.
 */
export const SELECTABLE_PAYMENT_METHODS: readonly PaymentMethod[] = ["DIRECT"] as const;

/**
 * Every method that moves money OUTSIDE TruConnect.
 *
 * Mirrors DIRECT_PAYMENT_METHODS in the backend's models/stock_order.py
 * exactly, and for the same reason it exists there: the answer to "is
 * this the direct rail?" decides the order's whole path. Direct means
 * the supplier releases stock against a promise, so the order is a
 * REQUEST and their accept/decline is real. Digital means the money
 * already moved, so it is a PURCHASE that needs no approval.
 */
export const DIRECT_PAYMENT_METHODS: readonly PaymentMethod[] = [
  "DIRECT",
  "CASH",
  "PROOF_OF_PAYMENT",
] as const;

export function isDirectPayment(method: PaymentMethod | null | undefined): boolean {
  return method != null && DIRECT_PAYMENT_METHODS.includes(method);
}

/**
 * What a person sees. Covers every value including the historical ones,
 * because an order placed last month still has to render.
 */
export const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  DIRECT: "Pay the supplier",
  // Historical. Labelled as they were at the time so a past order reads
  // the way the buyer remembers it, not relabelled to today's wording.
  CASH: "Cash",
  PROOF_OF_PAYMENT: "Proof of Payment",
  PAYFAST: "Card or EFT",
};

/** The one-line explanation under the option, for the picker. */
export const PAYMENT_METHOD_DESCRIPTIONS: Record<PaymentMethod, string> = {
  DIRECT: "Cash on delivery or collection, or pay by transfer",
  CASH: "Pay on delivery or collection",
  PROOF_OF_PAYMENT: "Pay the supplier directly, then send proof",
  PAYFAST: "Pay now by card or instant EFT",
};


/**
 * The label for whatever the server actually sent.
 *
 * TAKES A LOOSE STRING ON PURPOSE. Order payloads cross the wire, and a
 * build of this app can meet a value added to the backend after it
 * shipped -- indexing a strict Record with that would be a type error at
 * best and a blank cell at worst. Falling back to the raw value shows
 * the buyer SOMETHING true rather than nothing, which is the same
 * `?? order.paymentMethod` every call site was already writing by hand.
 */
export function paymentMethodLabel(method: string | null | undefined): string {
  if (!method) return "—";
  return PAYMENT_METHOD_LABELS[method as PaymentMethod] ?? method;
}
