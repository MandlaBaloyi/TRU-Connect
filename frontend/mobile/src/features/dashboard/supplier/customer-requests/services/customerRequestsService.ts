/**
 * Customer Requests — the ONLY boundary between this feature and its
 * data. Same rule/pattern as find-supplier/services/supplierSearchService.ts.
 */
import * as mockApi from "./mockCustomerRequestsService";
import * as httpApi from "./httpCustomerRequestsService";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const impl = USE_MOCK ? mockApi : httpApi;

export const getCustomerRequests = impl.getCustomerRequests;
export const getCustomerRequestDetail = impl.getCustomerRequestDetail;
export const approveRequest = impl.approveRequest;
export const declineRequest = impl.declineRequest;
