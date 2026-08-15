import type { ConnectionSummary } from "../types";

const latency = (ms = 400) => new Promise<void>((resolve) => setTimeout(resolve, ms));

const MOCK_CONNECTIONS: ConnectionSummary[] = [
  {
    id: "conn_001",
    name: "Mandla's Spaza Shop",
    connectedSince: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

export async function getMyConnections(): Promise<ConnectionSummary[]> {
  await latency();
  return MOCK_CONNECTIONS;
}
