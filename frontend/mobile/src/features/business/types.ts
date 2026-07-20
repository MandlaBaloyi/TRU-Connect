/**
 * Types mirroring the Business Domain (docs/04_DATABASE_DESIGN.txt,
 * Section 4.2) as collected through the Business Profile Setup wizard.
 */
export interface BusinessInfoStep {
  businessName: string;
  tradingName?: string;
  businessType: string;
  industry: string;
  yearsOperating: string;
  addressLine: string;
  latitude?: number;
  longitude?: number;
}

export interface OwnerInfoStep {
  ownerName: string;
  saIdNumber: string;
  phoneNumber: string;
  email: string;
}

export interface TradingInfoStep {
  monthlyRevenue: string;
  customersPerMonth: string;
  averageTransaction: string;
  primarySupplier?: string;
}

export interface DocumentsStep {
  idCopyUri?: string;
  businessPhotoUris: string[];
  tradingProofUri?: string;
  bankStatementUri?: string;
}

export interface BusinessProfileWizardState {
  businessInfo: Partial<BusinessInfoStep>;
  ownerInfo: Partial<OwnerInfoStep>;
  tradingInfo: Partial<TradingInfoStep>;
  documents: Partial<DocumentsStep>;
}
