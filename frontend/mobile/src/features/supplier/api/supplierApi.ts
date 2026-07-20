import { apiClient } from "@/services/api/apiClient";

/** Ref: docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.3 (Supplier Domain) */
export const supplierApi = {
  async getDashboard() {
    const { data } = await apiClient.get("/suppliers/me/dashboard");
    return data;
  },
};
