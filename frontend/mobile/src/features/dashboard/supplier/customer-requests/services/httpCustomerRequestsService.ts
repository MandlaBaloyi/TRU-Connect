/**
 * Customer Requests, REAL HTTP implementation — calls
 * /api/v1/supplier-discovery/customer-requests/* (the supplier-side
 * mirror of Find Supplier's business-side routes, same backend
 * domain: network/supplier_discovery). Selected by
 * services/customerRequestsService.ts when EXPO_PUBLIC_USE_MOCK_API=false.
 */
import { apiGet, apiPost, ApiError } from "@/services/api/apiClient";

import type { ConnectionRequestStatus, CustomerRequestDetail, CustomerRequestSummary } from "../types";

export async function getCustomerRequests(): Promise<CustomerRequestSummary[]> {
  const data = await apiGet<{ requests: CustomerRequestSummary[] }>("/supplier-discovery/customer-requests");
  return data.requests;
}

export async function getCustomerRequestDetail(id: string): Promise<CustomerRequestDetail | null> {
  try {
    return await apiGet<CustomerRequestDetail>(`/supplier-discovery/customer-requests/${id}`);
  } catch (error) {
    if (error instanceof ApiError && error.code === "REQUEST_NOT_FOUND") {
      return null;
    }
    throw error;
  }
}

export async function approveRequest(id: string): Promise<ConnectionRequestStatus> {
  const data = await apiPost<{ status: ConnectionRequestStatus }>(
    `/supplier-discovery/customer-requests/${id}/approve`
  );
  return data.status;
}

export async function declineRequest(id: string): Promise<ConnectionRequestStatus> {
  const data = await apiPost<{ status: ConnectionRequestStatus }>(
    `/supplier-discovery/customer-requests/${id}/decline`
  );
  return data.status;
}
