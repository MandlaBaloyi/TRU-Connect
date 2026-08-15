/**
 * Business search — the ONLY boundary between Find Business and its
 * data. Same rule as every other feature in this app: no hook/screen
 * ever imports mockBusinessSearchService or httpBusinessSearchService
 * directly, and none ever calls apiClient/fetch itself.
 *
 * getRecentSearches is NOT switched — always the same local store
 * regardless of EXPO_PUBLIC_USE_MOCK_API, same reasoning as Find
 * Supplier's own boundary file.
 */
import * as mockApi from "./mockBusinessSearchService";
import * as httpApi from "./httpBusinessSearchService";
import { getRecentSearches } from "./recentSearchesStore";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const impl = USE_MOCK ? mockApi : httpApi;

export const searchBusinesses = impl.searchBusinesses;
export const getBusinessProfile = impl.getBusinessProfile;
export const requestConnection = impl.requestConnection;
export const inviteBusiness = impl.inviteBusiness;

export { getRecentSearches };
