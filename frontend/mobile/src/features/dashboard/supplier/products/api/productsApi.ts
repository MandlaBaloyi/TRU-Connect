/**
 * Products — the ONLY boundary between this feature and its data. No
 * hook/screen/component ever calls apiClient directly, and no hook/
 * screen/component ever imports mockProductsApi or httpProductsApi
 * directly. Same rule as Order Book (see its own orderBookApi.ts).
 *
 * MUST be this exact literal expression, `process.env.EXPO_PUBLIC_X` --
 * Expo's babel plugin does a static text replacement at build time,
 * not a real runtime lookup.
 */
import * as mockApi from "./mockProductsApi";
import * as httpApi from "./httpProductsApi";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const impl = USE_MOCK ? mockApi : httpApi;

export const getProducts = impl.getProducts;
export const getProduct = impl.getProduct;
export const createProduct = impl.createProduct;
export const updateProduct = impl.updateProduct;
export const archiveProduct = impl.archiveProduct;
export const bulkUpdateStockStatus = impl.bulkUpdateStockStatus;
export const bulkAdjustPrice = impl.bulkAdjustPrice;
export const bulkArchiveProducts = impl.bulkArchiveProducts;

export { ProductsError } from "../types";
