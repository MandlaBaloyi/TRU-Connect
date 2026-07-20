/**
 * Shape of the aggregated dashboard payload.
 * Ref: docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.2
 * (GET /businesses/me/dashboard) and docs/07_DATA_AND_TRUST_ENGINE.txt
 * (Digital Business Profile / Business Health Score).
 */
export interface BusinessDashboardData {
  businessName: string;
  trustScore: number | null;
  todaySales: string;
  tradingActivityCount: number;
}
