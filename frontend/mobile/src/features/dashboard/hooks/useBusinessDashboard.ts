import { useQuery } from "@tanstack/react-query";
import { businessApi } from "@/features/business/api/businessApi";
import type { BusinessDashboardData } from "../types";

/**
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Business Dashboard)
 * and docs/07_DATA_AND_TRUST_ENGINE.txt (Business Health Score).
 */
export function useBusinessDashboard() {
  return useQuery<BusinessDashboardData>({
    queryKey: ["business-dashboard"],
    queryFn: businessApi.getDashboard,
  });
}
