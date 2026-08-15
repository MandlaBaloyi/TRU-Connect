/**
 * Supplier Requests, REAL HTTP implementation — calls
 * /api/v1/supplier-discovery/supplier-requests/* (the business-side
 * mirror of Find Business's supplier-side routes, same backend
 * domain: network/supplier_discovery). Selected by
 * services/supplierRequestsService.ts when EXPO_PUBLIC_USE_MOCK_API=false.
 */
import { apiGet, apiPost, ApiError } from "@/services/api/apiClient";

import type { ConnectionRequestStatus, SupplierRequestDetail, SupplierRequestSummary } from "../types";

export async function getSupplierRequests(): Promise<SupplierRequestSummary[]> {
  const data = await apiGet<{ requests: SupplierRequestSummary[] }>("/supplier-discovery/supplier-requests");
  return data.requests;
}

export async function getSupplierRequestDetail(id: string): Promise<SupplierRequestDetail | null> {
  try {
    return await apiGet<SupplierRequestDetail>(`/supplier-discovery/supplier-requests/${id}`);
  } catch (error) {
    if (error instanceof ApiError && error.code === "REQUEST_NOT_FOUND") {
      return null;
    }
    throw error;
  }
}

export async function approveRequest(id: string): Promise<ConnectionRequestStatus> {
  const data = await apiPost<{ status: ConnectionRequestStatus }>(
    `/supplier-discovery/supplier-requests/${id}/approve`
  );
  return data.status;
}

export async function declineRequest(id: string): Promise<ConnectionRequestStatus> {
  const data = await apiPost<{ status: ConnectionRequestStatus }>(
    `/supplier-discovery/supplier-requests/${id}/decline`
  );
  return data.status;
}
