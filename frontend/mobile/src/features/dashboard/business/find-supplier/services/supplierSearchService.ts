/**
 * Supplier search — the ONLY boundary between Find Supplier and its
 * data. Same rule as every other feature in this app (see
 * business-profile/api/businessProfileApi.ts's own docstring): no
 * hook/screen ever imports mockSupplierSearchService or
 * httpSupplierSearchService directly, and none ever calls
 * apiClient/fetch itself.
 *
 * getRecentSearches is NOT switched — it's always the same local
 * store regardless of EXPO_PUBLIC_USE_MOCK_API, since it was never
 * backend data (see recentSearchesStore.ts's own docstring).
 */
import * as mockApi from "./mockSupplierSearchService";
import * as httpApi from "./httpSupplierSearchService";
import { getRecentSearches } from "./recentSearchesStore";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const impl = USE_MOCK ? mockApi : httpApi;

export const searchSuppliers = impl.searchSuppliers;
export const getSupplierProfile = impl.getSupplierProfile;
export const requestConnection = impl.requestConnection;
export const endConnection = impl.endConnection;
export const reportSupplier = impl.reportSupplier;
export const inviteSupplier = impl.inviteSupplier;
export const getSupplierProducts = impl.getSupplierProducts;
export const getSupplierProfileProducts = impl.getSupplierProfileProducts;
export const getSupplierProductCategories = impl.getSupplierProductCategories;
export const getSupplierProduct = impl.getSupplierProduct;
export const getRelatedProducts = impl.getRelatedProducts;

export { getRecentSearches };
