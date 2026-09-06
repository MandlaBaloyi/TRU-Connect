import * as mockApi from "./mockGeocodingService";
import * as httpApi from "./httpGeocodingService";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const impl = USE_MOCK ? mockApi : httpApi;

export const reverseGeocode = impl.reverseGeocode;
export const suggestAddress = impl.suggestAddress;
export const retrieveAddress = impl.retrieveAddress;
