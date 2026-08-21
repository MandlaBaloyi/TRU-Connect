/**
 * Bulk Import — the ONLY boundary between this feature and its data,
 * same rule as every other feature's own api switch in this app (see
 * products/api/productsApi.ts's own docstring for the full reasoning).
 */
import * as mockApi from "./mockBulkImportApi";
import * as httpApi from "./httpBulkImportApi";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const impl = USE_MOCK ? mockApi : httpApi;

export const submitImport = impl.submitImport;
export const getImportJob = impl.getImportJob;
export const getImportJobErrors = impl.getImportJobErrors;
export const listImportJobs = impl.listImportJobs;
