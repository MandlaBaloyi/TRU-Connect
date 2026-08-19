/**
 * Inventory — the ONLY boundary between this feature and its data,
 * same rule as every other feature's own api switch in this app.
 */
import * as mockApi from "./mockInventoryApi";
import * as httpApi from "./httpInventoryApi";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const impl = USE_MOCK ? mockApi : httpApi;

export const getInventoryList = impl.getInventoryList;
export const getInventoryItem = impl.getInventoryItem;
export const getInventorySummary = impl.getInventorySummary;
export const adjustStock = impl.adjustStock;
export const setLowStockThreshold = impl.setLowStockThreshold;
export const getInventorySettings = impl.getInventorySettings;
export const updateInventorySettings = impl.updateInventorySettings;

export { InventoryError } from "../types";
