/**
 * The seam between the supplier portal's auth screens and the backend.
 *
 * NOT WIRED YET, AND DELIBERATELY SO. The forms are real, the validation
 * is real, and the shapes below match what the Flask auth domain already
 * accepts -- but the transport is a decision that has not been made in
 * code yet, and guessing it here would bake in the wrong one.
 *
 * WHY THE TRANSPORT IS NOT JUST "SEND THE JWT". The mobile app stores a
 * JWT and sends `Authorization: Bearer`. A browser must NOT do that:
 * anything held in localStorage is readable by any XSS on the page. The
 * portal needs an httpOnly, Secure, SameSite cookie issued by the same
 * backend, plus CSRF protection, which bearer tokens do not need. That
 * is real backend work (see V2_00 section 2.10) and it lands before
 * these functions do.
 *
 * UNTIL THEN these throw rather than silently pretending to succeed. A
 * form that appears to log you in and does not is worse than a form that
 * says it is not connected yet.
 */

export interface SupplierSignUpPayload {
  /** The trading name businesses will see. Required. */
  businessName: string;
  /** The person's own name. Optional -- the business name is what matters. */
  ownerName?: string;
  email: string;
  phone: string;
  password: string;
}

export interface SignInPayload {
  email: string;
  password: string;
}

export class NotWiredError extends Error {
  constructor() {
    super(
      "Supplier accounts are not connected yet. The portal is being built — please check back shortly.",
    );
    this.name = "NotWiredError";
  }
}

export async function signUpSupplier(
  _payload: SupplierSignUpPayload,
): Promise<never> {
  throw new NotWiredError();
}

export async function signIn(_payload: SignInPayload): Promise<never> {
  throw new NotWiredError();
}
