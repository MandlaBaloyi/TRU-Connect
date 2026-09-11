/**
 * Supplier verification status, as the backend reports it.
 *
 * THE SHAPE IS BUILT FOR THE BANNER, not for a debugger -- headline
 * and detail arrive as finished sentences rather than as a status the
 * client has to translate. That is deliberate: this is text a supplier
 * reads on every screen, and wording that lives in one place on the
 * server can be fixed without an app release.
 */
export type SupplierVerificationState = "unverified" | "pending" | "verified";

export interface VerificationStatus {
  /** Null only for a profile row that predates the column. */
  status: SupplierVerificationState | null;
  /** THE FIELD THAT MATTERS. Everything else is presentation. */
  visibleToBuyers: boolean;
  headline: string;
  detail: string;
}
