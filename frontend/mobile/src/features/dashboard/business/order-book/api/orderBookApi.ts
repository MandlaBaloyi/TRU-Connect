/**
 * Order Book — the ONLY boundary between this feature and its data.
 * Same rule as Loan Book: no hook/screen/component ever calls fetch or
 * apiClient directly, and no hook/screen/component ever imports
 * mockOrderBookApi or httpOrderBookApi directly. Only this file does.
 *
 * MUST be this exact literal expression, `process.env.EXPO_PUBLIC_X` —
 * Expo's babel plugin does a static text replacement at build time, not
 * a real runtime lookup. See useCurrentUserId.ts / loanBookApi.ts for
 * the full explanation; same constraint applies here verbatim.
 */

import * as mockApi from "./mockOrderBookApi";
import * as httpApi from "./httpOrderBookApi";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const impl = USE_MOCK ? mockApi : httpApi;

export const getOrderBookSummary = impl.getOrderBookSummary;
export const getOrders = impl.getOrders;
export const getOrder = impl.getOrder;
export const searchCustomers = impl.searchCustomers;
export const getOrderHistory = impl.getOrderHistory;
export const createOrder = impl.createOrder;
export const completeOrder = impl.completeOrder;
export const cancelOrder = impl.cancelOrder;

export const getTrash = impl.getTrash;
export const deleteOrder = impl.deleteOrder;
export const restoreOrder = impl.restoreOrder;
export const deleteCustomer = impl.deleteCustomer;
export const restoreCustomer = impl.restoreCustomer;
export const clearAllCompletedNow = impl.clearAllCompletedNow;
export const runAutoClearSweep = impl.runAutoClearSweep;
export const getDailyRevenue = impl.getDailyRevenue;
export const getAutoClearSettings = impl.getAutoClearSettings;
export const setAutoClearSetting = impl.setAutoClearSetting;

export { OrderBookError } from "./mockOrderBookApi";
