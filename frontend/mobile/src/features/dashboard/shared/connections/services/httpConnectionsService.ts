/**
 * My Connections, REAL HTTP implementation — calls the actual
 * GET /api/v1/supplier-discovery/connections, verified end-to-end
 * against real Postgres before this file was written (see this
 * feature's own types.ts backend-contract note). One call works
 * correctly for either role — no role param needed, the backend
 * reads it from the JWT.
 */
import { apiGet } from "@/services/api/apiClient";

import type { ConnectionSummary } from "../types";

export async function getMyConnections(): Promise<ConnectionSummary[]> {
  const data = await apiGet<{ connections: ConnectionSummary[] }>("/supplier-discovery/connections");
  return data.connections;
}
