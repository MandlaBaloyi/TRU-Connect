/**
 * Types mirroring the Supplier Domain (docs/04_DATABASE_DESIGN.txt,
 * Section 4.3) account-registration fields collected in Phase 1.
 */
export interface SupplierRegistrationInfo {
  businessName: string;
  registrationNumber?: string;
  ownerName: string;
  phoneNumber: string;
  email: string;
}
