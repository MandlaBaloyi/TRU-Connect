/**
 * Business Profile — the ONLY boundary between this feature and its
 * data. Same rule as every other feature: no hook/screen/component
 * ever calls fetch/apiClient directly, and none ever imports
 * mockBusinessProfileApi or httpBusinessProfileApi directly.
 */

import * as mockApi from "./mockBusinessProfileApi";
import * as httpApi from "./httpBusinessProfileApi";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const impl = USE_MOCK ? mockApi : httpApi;

export const getBusinessProfile = impl.getBusinessProfile;
export const updateBusinessDetails = impl.updateBusinessDetails;
export const updateContactDetails = impl.updateContactDetails;
export const updateLocation = impl.updateLocation;
export const updateTradingDetails = impl.updateTradingDetails;
export const updateOperatingHistory = impl.updateOperatingHistory;
export const updateSupplierInfo = impl.updateSupplierInfo;

export { BusinessProfileError } from "./mockBusinessProfileApi";
