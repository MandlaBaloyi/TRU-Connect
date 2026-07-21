/*******
 import { apiClient } from "@/services/api/apiClient";
import { BusinessProfileWizardState } from "../types";


 * Feature-level API bindings for the Business Domain, built on top of the
 * shared apiClient (src/services/api/apiClient.ts).
 * Ref: docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.2 (Business Domain
 * endpoints) and Section 5.6 (Verification Domain - document submission).
 
export const businessApi = {
  async submitProfileSetup(state: BusinessProfileWizardState) {
    const { data } = await apiClient.put("/businesses/me", {
      ...state.businessInfo,
      ...state.ownerInfo,
      ...state.tradingInfo,
    });
    return data;
  },

  async uploadDocument(documentType: string, fileUri: string) {
    const formData = new FormData();
    formData.append("document_type", documentType);
    // @ts-expect-error - React Native FormData file shape
    formData.append("file", { uri: fileUri, name: `${documentType}.jpg`, type: "image/jpeg" });
    const { data } = await apiClient.post("/businesses/me/documents", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  async getDashboard() {
    const { data } = await apiClient.get("/businesses/me/dashboard");
    return data;
  },

  async getDigitalBusinessProfile() {
    const { data } = await apiClient.get("/businesses/me/profile");
    return data;
  },
};    
*************/
