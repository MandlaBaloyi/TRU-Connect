import type { ConnectionSummary, EndedConnectionSummary } from "../types";

const latency = (ms = 400) => new Promise<void>((resolve) => setTimeout(resolve, ms));

const MOCK_CONNECTIONS: ConnectionSummary[] = [
  {
    id: "conn_001",
    name: "Mandla's Spaza Shop",
    // Matches mockProductsApi.ts's own MOCK_SUPPLIER_ID -- so tapping
    // this connection in mock mode genuinely navigates to a real,
    // populated mock product catalogue, not a dead end.
    otherPartyId: "mock-supplier-001",
    connectedSince: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

const MOCK_ENDED_CONNECTIONS: EndedConnectionSummary[] = [
  {
    id: "conn_ended_001",
    name: "Old Fragrance Supplier",
    otherPartyId: "sup_002",
    endedReason: "FOUND_BETTER_SUPPLIER",
    endedDetails: "Prices were better elsewhere",
    endedAt: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

export async function getMyConnections(): Promise<ConnectionSummary[]> {
  await latency();
  return MOCK_CONNECTIONS;
}

export async function getEndedConnections(): Promise<EndedConnectionSummary[]> {
  await latency();
  return MOCK_ENDED_CONNECTIONS;
}
