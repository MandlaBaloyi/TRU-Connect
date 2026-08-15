/**
 * Supplier Requests service — MOCK implementation. Mirrors
 * supplier/customer-requests/services/mockCustomerRequestsService.ts
 * exactly.
 */
import type { ConnectionRequestStatus, SupplierRequestDetail, SupplierRequestSummary } from "../types";

const latency = (ms = 400) => new Promise<void>((resolve) => setTimeout(resolve, ms));

interface MockRequest {
  id: string;
  businessName: string;
  ownerName: string;
  category: string;
  location: string;
  phone: string;
  email: string;
  requestedAt: string;
  status: ConnectionRequestStatus;
}

let MOCK_REQUESTS: MockRequest[] = [
  {
    id: "sreq_001",
    businessName: "ABC Wholesale",
    ownerName: "Naledi Mahlangu",
    category: "Wholesale beverages",
    location: "Polokwane",
    phone: "+27712345678",
    email: "orders@abcwholesale.co.za",
    requestedAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    status: "PENDING",
  },
];

function maskEmail(email: string): string {
  const [local, domain] = email.split("@");
  if (!domain) return "***";
  if (local.length <= 2) return `${local[0]}*@${domain}`;
  return `${local[0]}${"*".repeat(local.length - 2)}${local[local.length - 1]}@${domain}`;
}

function maskPhone(phone: string): string {
  const digits = phone.replace(/\D/g, "");
  if (digits.length < 6) return "***";
  const last4 = digits.slice(-4);
  return `${phone.slice(0, 3)} ${digits.slice(2, 4)} *** ${last4.slice(0, 2)} ${last4.slice(2)}`;
}

export async function getSupplierRequests(): Promise<SupplierRequestSummary[]> {
  await latency();
  return MOCK_REQUESTS.filter((r) => r.status === "PENDING").map((r) => ({
    id: r.id,
    businessName: r.businessName,
    requestedAt: r.requestedAt,
    status: r.status,
  }));
}

export async function getSupplierRequestDetail(id: string): Promise<SupplierRequestDetail | null> {
  await latency(300);
  const request = MOCK_REQUESTS.find((r) => r.id === id);
  if (!request) return null;
  return {
    id: request.id,
    businessName: request.businessName,
    ownerName: request.ownerName,
    category: request.category,
    location: request.location,
    maskedPhone: maskPhone(request.phone),
    maskedEmail: maskEmail(request.email),
    requestedAt: request.requestedAt,
    status: request.status,
  };
}

export async function approveRequest(id: string): Promise<ConnectionRequestStatus> {
  await latency(400);
  MOCK_REQUESTS = MOCK_REQUESTS.map((r) => (r.id === id ? { ...r, status: "ACTIVE" } : r));
  return "ACTIVE";
}

export async function declineRequest(id: string): Promise<ConnectionRequestStatus> {
  await latency(400);
  MOCK_REQUESTS = MOCK_REQUESTS.map((r) => (r.id === id ? { ...r, status: "DECLINED" } : r));
  return "DECLINED";
}
