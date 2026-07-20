import { create } from "zustand";
import { BusinessProfileWizardState } from "../types";

/**
 * In-memory store carrying the Business Profile Setup wizard's state
 * across its 5 steps (docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt,
 * Screen 7), until final submission via businessApi.submitProfileSetup.
 * zustand is an approved dependency for this project.
 */
interface WizardStore extends BusinessProfileWizardState {
  setBusinessInfo: (v: Partial<BusinessProfileWizardState["businessInfo"]>) => void;
  setOwnerInfo: (v: Partial<BusinessProfileWizardState["ownerInfo"]>) => void;
  setTradingInfo: (v: Partial<BusinessProfileWizardState["tradingInfo"]>) => void;
  setDocuments: (v: Partial<BusinessProfileWizardState["documents"]>) => void;
  reset: () => void;
}

const initialState: BusinessProfileWizardState = {
  businessInfo: {},
  ownerInfo: {},
  tradingInfo: {},
  documents: { businessPhotoUris: [] },
};

export const useBusinessProfileWizard = create<WizardStore>((set) => ({
  ...initialState,
  setBusinessInfo: (v) => set((s) => ({ businessInfo: { ...s.businessInfo, ...v } })),
  setOwnerInfo: (v) => set((s) => ({ ownerInfo: { ...s.ownerInfo, ...v } })),
  setTradingInfo: (v) => set((s) => ({ tradingInfo: { ...s.tradingInfo, ...v } })),
  setDocuments: (v) => set((s) => ({ documents: { ...s.documents, ...v } })),
  reset: () => set(initialState),
}));
