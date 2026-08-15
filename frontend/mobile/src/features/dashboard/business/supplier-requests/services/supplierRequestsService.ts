/**
 * Supplier Requests — the ONLY boundary between this feature and its
 * data. Same rule/pattern as every other feature in this app.
 */
import * as mockApi from "./mockSupplierRequestsService";
import * as httpApi from "./httpSupplierRequestsService";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const impl = USE_MOCK ? mockApi : httpApi;

export const getSupplierRequests = impl.getSupplierRequests;
export const getSupplierRequestDetail = impl.getSupplierRequestDetail;
export const approveRequest = impl.approveRequest;
export const declineRequest = impl.declineRequest;
