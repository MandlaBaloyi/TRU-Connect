/**
 * My Connections, REAL HTTP implementation — calls the actual
 * GET /api/v1/supplier-discovery/connections, verified end-to-end
 * against real Postgres before this file was written (see this
 * feature's own types.ts backend-contract note). One call works
 * correctly for either role — no role param needed, the backend
 * reads it from the JWT.
 */
import { apiGet } from "@/services/api/apiClient";

import type { ConnectionSummary, EndedConnectionSummary } from "../types";

interface ApiConnectionSummary {
  id: string;
  name: string;
  other_party_id: string | null;
  connectedSince: string | null;
  photoUrl: string | null;
  ownerName: string | null;
  // Defaulted in the mapper above rather than required here: an
  // older backend that has not shipped the ledger yet should render
  // a plain row, not crash the Community tab.
  orderCount?: number;
  lastOrderAt?: string | null;
  typicalGapDays?: number | null;
  isOverdue?: boolean;
  openOrder?: { id: string; status: string; submittedAt: string | null } | null;
}

/**
 * REAL GAP FOUND DURING REVIEW: this file used to type apiGet directly
 * against ConnectionSummary with no explicit mapping at all -- worked
 * by accident only because every field so far happened to already be
 * camelCase on the backend. other_party_id (snake_case, the field this
 * whole search/connections redesign added) would have silently landed
 * as undefined forever, despite the type system confidently claiming
 * otherPartyId: string | null. Explicit mapping, matching how every
 * other real HTTP service in this app already does this (see
 * products/api/httpProductsApi.ts's own fromApiProduct).
 */
function fromApiConnectionSummary(dto: ApiConnectionSummary): ConnectionSummary {
  return {
    id: dto.id,
    name: dto.name,
    otherPartyId: dto.other_party_id,
    connectedSince: dto.connectedSince,
    photoUrl: dto.photoUrl,
    ownerName: dto.ownerName,
    orderCount: dto.orderCount ?? 0,
    lastOrderAt: dto.lastOrderAt ?? null,
    typicalGapDays: dto.typicalGapDays ?? null,
    isOverdue: dto.isOverdue ?? false,
    openOrder: dto.openOrder ?? null,
  };
}

export async function getMyConnections(): Promise<ConnectionSummary[]> {
  const data = await apiGet<{ connections: ApiConnectionSummary[] }>("/supplier-discovery/connections");
  return data.connections.map(fromApiConnectionSummary);
}

/** No explicit mapping needed here, unlike getMyConnections above --
 *  list_ended_connections' own dict is already hand-built as camelCase
 *  directly in Python (matching list_supplier_products/
 *  get_supplier_product's own convention), not the snake_case
 *  other_party_id shape get_my_connections used before this file's own
 *  fromApiConnectionSummary mapping was added to fix it. */
export async function getEndedConnections(): Promise<EndedConnectionSummary[]> {
  const data = await apiGet<{ connections: EndedConnectionSummary[] }>("/supplier-discovery/connections/ended");
  return data.connections;
}
