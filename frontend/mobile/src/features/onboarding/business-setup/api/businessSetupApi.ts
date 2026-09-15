/**
 * Business setup — the ONLY boundary between this feature and its
 * data. Same rule as every other feature: no hook, screen or component
 * calls apiClient directly, and none imports the mock or http module
 * by name.
 */

import * as mockApi from "./mockBusinessSetupApi";
import * as httpApi from "./httpBusinessSetupApi";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const impl = USE_MOCK ? mockApi : httpApi;

export const getSetupState = impl.getSetupState;
